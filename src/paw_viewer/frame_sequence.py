import numpy as np
import pyglet
from pyglet.gl import GL_RGBA32F


class FrameSequence:
    """Represents a sequence of frames (images) and the texture used for rendering them."""

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

        image = active_frames[0]
        self.texture = pyglet.image.Texture.create(
            width=image.shape[1], height=image.shape[0], internalformat=GL_RGBA32F
        )
        self.update_texture()

    @property
    def frames(self):
        return self.sources[self.active_source]

    def active_source_name(self):
        return self.names[self.active_source]

    def animation_step(self, dt):
        if not self.running:
            # just in case - this should not be called when not running
            return
        self.frame_index = (self.frame_index + 1) % self.num_frames
        self.update_texture()

    def update_texture(self):
        from ctypes import POINTER, c_float

        from pyglet import gl

        active_frames = self.sources[self.active_source]
        image = active_frames[self.frame_index]

        gl.glBindTexture(self.texture.target, self.texture.id)
        image_f32: np.ndarray = image[::-1, :, :].astype(np.float32) / 255
        gl.glTexImage2D(
            self.texture.target,
            0,
            gl.GL_RGBA32F,  # internal format
            self.texture.width,
            self.texture.height,
            0,
            gl.GL_RGBA,
            gl.GL_FLOAT,
            image_f32.ctypes.data_as(POINTER(c_float)),
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
        self.update_texture()

    def go_end(self):
        self.frame_index = self.num_frames - 1
        self.update_texture()

    def go_next(self):
        self.frame_index = (self.frame_index + 1) % self.num_frames
        self.update_texture()

    def go_previous(self):
        self.frame_index = (self.frame_index - 1) % self.num_frames
        self.update_texture()

    def next_source(self):
        self.active_source = (self.active_source + 1) % len(self.sources)
        self.update_texture()

    def previous_source(self):
        self.active_source = (self.active_source - 1) % len(self.sources)
        self.update_texture()
