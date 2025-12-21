from dataclasses import dataclass

import numpy as np
import pyglet


@dataclass
class FrameSequence:
    frames: np.ndarray
    fps: float = 30


class FrameSequenceAnimation:
    """Represents a sequence of frames (images) and the texture used for rendering them."""

    def __init__(self, frame_sequence: FrameSequence):
        self.frames = frame_sequence.frames
        self.fps = frame_sequence.fps
        self.num_frames = frame_sequence.frames.shape[0]
        self.frame_index = 0
        self.running = False

        image = self.frames[0]
        self.image_data = pyglet.image.ImageData(
            width=image.shape[1],
            height=image.shape[0],
            fmt="RGBA",
            data=image.tobytes(),
            pitch=-image.shape[1] * 4,
        )
        self.texture = self.image_data.get_texture()

    def animation_step(self, dt):
        if not self.running:
            # just in case - this should not be called when not running
            return
        self.frame_index = (self.frame_index + 1) % self.num_frames
        self.update_texture()

    def update_texture(self):
        image = self.frames[self.frame_index]
        self.image_data.set_data(
            fmt="RGBA",
            pitch=-image.shape[1] * 4,
            data=image.tobytes(),
        )
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
