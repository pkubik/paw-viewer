import numpy as np
import pyglet
from pyglet.gl import GL_NEAREST


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

        T, H, W, _ = self.sources[self.active_source].shape
        if any(source.shape[:3] != (T, H, W) for source in self.sources):
            raise ValueError("all sources must have the same shape")

        active_frames = self.sources[self.active_source]
        self.num_frames = active_frames.shape[0]
        self.frame_index = 0
        self.running = False

        self.per_source_textures = [
            [
                pyglet.image.Texture.create(
                    width=W,
                    height=H,
                    min_filter=GL_NEAREST,
                    mag_filter=GL_NEAREST,
                )
                for _ in range(T)
            ]
            for _ in self.sources
        ]
        self._update_textures()

    @property
    def frames(self):
        return self.sources[self.active_source]

    @property
    def active_textures(self):
        return self.per_source_textures[self.active_source]

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

    def _update_textures(self):
        """Should be called only after setting sources (i.e. in init)"""
        from ctypes import POINTER, c_uint8

        from pyglet import gl

        for frames, textures in zip(self.sources, self.per_source_textures):
            for image, texture in zip(frames, textures):
                image = (
                    (255 * np.sign(image) * np.abs(image) ** (1 / 2.2))
                    .clip(0, 255)
                    .astype(np.uint8)
                )

                gl.glBindTexture(texture.target, texture.id)
                gl.glTexImage2D(
                    texture.target,  # target
                    0,  # level
                    gl.GL_RGBA8,  # internalformat
                    texture.width,  # width
                    texture.height,  # height
                    0,  # border
                    gl.GL_RGBA,  # format
                    gl.GL_UNSIGNED_BYTE,  # type
                    image.ctypes.data_as(POINTER(c_uint8)),  # pixels
                )

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
