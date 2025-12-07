import pyglet

from paw_viewer.frame_sequence import FrameSequence
from paw_viewer.frame_view import FrameView
from paw_viewer.slider import Slider


class ViewerWindow(pyglet.window.Window):
    def __init__(
        self, frame_sequence: FrameSequence, caption="paw", resizable=True, **kwargs
    ):
        super().__init__(caption=caption, resizable=resizable, **kwargs)
        self.batch = pyglet.graphics.Batch()
        pyglet.gl.glClearColor(0.05, 0.08, 0.06, 1)
        self.label = pyglet.text.Label("Zoom: 100%", x=5, y=5, batch=self.batch)

        self.frame_sequence = frame_sequence
        self.key_state = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_state)

        self.frame_view = FrameView(
            self.width,
            self.height,
            self.frame_sequence,
            batch=self.batch,
        )
        self.push_handlers(self.frame_view)

        self.slider_margin = 200
        self.slider = Slider(
            x=self.slider_margin,
            y=20,
            length=self.width - 2 * self.slider_margin,
            steps=self.frame_sequence.num_frames,
            batch=self.batch,
        )
        self.push_handlers(self.slider)

        @self.slider.event
        def on_change(value):
            self.frame_sequence.frame_index = value
            self.frame_sequence.update_texture()

    def on_resize(self, width: int, height: int):
        self.slider.length = self.width - 2 * self.slider_margin
        self.slider.update_geometry()
        return super().on_resize(width, height)

    def on_draw(self):
        self.frame_view.handle_keys(self.key_state)
        self.slider.update_step(self.frame_sequence.frame_index)
        self.label.text = f"Zoom: {int(self.frame_view.zoom_level.scale() * 100)}%"
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        if pyglet.window.key.MOD_CTRL & modifiers:
            if symbol == pyglet.window.key.Q:
                self.close()
        if symbol == pyglet.window.key.ESCAPE:
            return pyglet.event.EVENT_HANDLED


def show_video_array(video_array, fps: float = 30):
    frame_sequence = FrameSequence(video_array, fps=fps)
    viewer_window = ViewerWindow(frame_sequence=frame_sequence)

    pyglet.app.run()
