import numpy as np
import pyglet


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
        self.image_data = pyglet.image.ImageData(
            width=image.shape[1],
            height=image.shape[0],
            fmt="RGBA",
            data=image.tobytes(),
            pitch=-image.shape[1] * 4,
        )
        self.texture = self.image_data.get_texture()

    @property
    def frames(self):
        return self.sources[self.active_source]

    def animation_step(self, dt):
        if not self.running:
            # just in case - this should not be called when not running
            return
        self.frame_index = (self.frame_index + 1) % self.num_frames
        self.update_texture()

    def update_texture(self):
        active_frames = self.sources[self.active_source]
        image = active_frames[self.frame_index]
        self.image_data.set_data(
            fmt="RGBA",
            pitch=-image.shape[1] * 4,
            data=image.tobytes(),
        )
        # TODO: This is rather expensive
        #       Consider keeping whole array as texture
        #       and only update the coords
        self.texture.blit_into(self.image_data, 0, 0, 0)

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
