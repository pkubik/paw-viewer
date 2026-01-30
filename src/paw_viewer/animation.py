import numpy as np
import pyglet
from pyglet.gl import GL_NEAREST
import ctypes


DTYPE_TO_GL_FORMAT = {
    np.dtype(np.uint8): pyglet.gl.GL_RGBA8,
    np.dtype(np.float16): pyglet.gl.GL_RGBA16F,
    np.dtype(np.float32): pyglet.gl.GL_RGBA32F,
}

DTYPE_TO_CTYPE = {
    np.dtype(np.uint8): ctypes.POINTER(ctypes.c_uint8),
    np.dtype(np.float16): ctypes.POINTER(ctypes.c_uint16),
    np.dtype(np.float32): ctypes.POINTER(ctypes.c_float),
}

DTYPE_TO_GL_TYPE = {
    np.dtype(np.uint8): pyglet.gl.GL_UNSIGNED_BYTE,
    np.dtype(np.float16): pyglet.gl.GL_HALF_FLOAT,
    np.dtype(np.float32): pyglet.gl.GL_FLOAT,
}


class Animation:
    """
    Represents a sequence of frames split into multiple sources.

    Each source represent a different way of capturing the same scene,
    e.g. final image color with different graphic settings, texture albedos, depth.

    Each source capture consists of the same number of same-sized frames.
    """

    def __init__(self, sources: dict[str, np.ndarray], fps: float = 30):
        if len(sources) == 0:
            raise ValueError("sources must not be empty")
        self.sources = list(sources.values())
        self.names = list(sources.keys())
        self.fps = fps
        self.active_source = 0
        self.gamma = 1.0
        self.exposure = 1.0

        T, H, W, _ = self.sources[self.active_source].shape

        if self.sources[self.active_source].dtype != np.uint8:
            self.gamma = 2.2

        active_frames = self.sources[self.active_source]
        self.num_frames = active_frames.shape[0]
        self.frame_index = 0
        self.running = False

        self.per_source_textures = [
            [self._create_texture(source[t]) for t in range(T)]
            for source in self.sources
        ]

    def _create_texture(self, image: np.ndarray) -> pyglet.image.Texture:
        H, W, C = image.shape
        assert C == 4, "Only RGBA images are supported"

        texture = pyglet.image.Texture.create(
            width=W,
            height=H,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            internalformat=DTYPE_TO_GL_FORMAT[image.dtype],
        )
        from pyglet import gl

        gl.glBindTexture(texture.target, texture.id)
        gl.glTexImage2D(
            texture.target,  # target
            0,  # level
            DTYPE_TO_GL_FORMAT[image.dtype],  # internalformat
            texture.width,  # width
            texture.height,  # height
            0,  # border
            gl.GL_RGBA,  # format
            DTYPE_TO_GL_TYPE[image.dtype],  # type
            image.ctypes.data_as(DTYPE_TO_CTYPE[image.dtype]),  # pixels
        )
        return texture

    @property
    def frames(self):
        return self.sources[self.active_source]

    @property
    def active_textures(self):
        return self.per_source_textures[self.active_source]

    @property
    def main_texture(self) -> pyglet.image.Texture:
        return self.per_source_textures[0][self.frame_index]

    @property
    def active_texture(self) -> pyglet.image.Texture:
        return self.active_textures[self.frame_index]

    def active_source_name(self):
        return self.names[self.active_source]

    def animation_step(self, dt):
        if not self.running:
            # just in case - this should not be called when not running
            return
        self.frame_index = (self.frame_index + 1) % self.num_frames

    def frame_as_uint8(self, t: int | None = None) -> np.ndarray:
        if t is None:
            t = self.frame_index
        frame = self.frames[t]
        if frame.dtype != np.uint8:
            frame = (
                (255 * np.pow(np.abs(frame * self.exposure), 1 / self.gamma))
                .clip(0, 255)
                .astype(np.uint8)
            )
        return frame

    def start(self):
        pyglet.clock.schedule_interval(self.animation_step, 1 / self.fps)
        self.running = True

    def stop(self):
        pyglet.clock.unschedule(self.animation_step)
        self.running = False

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def go_start(self):
        self.frame_index = 0

    def go_end(self):
        self.frame_index = self.num_frames - 1

    def go_next(self):
        self.frame_index = (self.frame_index + 1) % self.num_frames

    def go_previous(self):
        self.frame_index = (self.frame_index - 1) % self.num_frames

    def next_source(self):
        self.active_source = (self.active_source + 1) % len(self.sources)

    def previous_source(self):
        self.active_source = (self.active_source - 1) % len(self.sources)
