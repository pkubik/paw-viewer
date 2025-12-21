import os
from pathlib import Path

import numpy as np
import pyglet

from paw_viewer import io
from paw_viewer.frame_sequence import FrameSequence, FrameSequenceAnimation
from paw_viewer.frame_view import FrameView
from paw_viewer.slider import Slider


class ViewerWindow(pyglet.window.Window):
    def __init__(
        self,
        caption="paw",
        resizable=True,
        outputs_root: str | Path | None = None,
        **kwargs,
    ):
        super().__init__(caption=caption, resizable=resizable, **kwargs)

        if outputs_root is None:
            outputs_root = Path(os.environ.get("PAW_OUTPUTS_ROOT", "."))
        self.outputs_root = Path(outputs_root)

        self.overlay_group = pyglet.graphics.Group(order=8)
        self.batch = pyglet.graphics.Batch()
        pyglet.gl.glClearColor(0.05, 0.08, 0.06, 1)

        self.key_state = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_state)

        self.frame_view = FrameView(
            self.width,
            self.height,
            batch=self.batch,
        )
        self.push_handlers(self.frame_view)

        self.slider_margin = 200
        self.slider = Slider(
            x=self.slider_margin,
            y=20,
            length=self.width - 2 * self.slider_margin,
            steps=1,
            batch=self.batch,
            parent_group=self.overlay_group,
        )
        self.push_handlers(self.slider)

        @self.slider.event
        def on_change(value):
            animation = self.frame_view.active_animation()
            if animation is not None:
                animation.frame_index = value
                animation.update_texture()

        self.label = pyglet.text.Label(
            "Zoom: 100%",
            x=5,
            y=5,
            batch=self.batch,
            group=self.overlay_group,
        )

    def add_animations(self, animations: dict[str, FrameSequenceAnimation]):
        for name, animation in animations.items():
            self.frame_view.add_animation(name, animation)

        self.frame_view.set_active_animation(-1)
        animation = self.frame_view.active_animation()
        if animation is not None:
            self.slider.total_steps = animation.num_frames
            self.slider.current_step = animation.frame_index
            self.slider.update_geometry()

    def on_resize(self, width: int, height: int):
        if self.invalid:
            # For some reason this event is triggered for uninitialized window,
            # that is being created after closing a previous one
            return super().on_resize(width, height)
        self.slider.length = self.width - 2 * self.slider_margin
        self.slider.update_geometry()
        return super().on_resize(width, height)

    def on_draw(self):
        self.frame_view.handle_keys(self.key_state)
        self.slider.update_step(self.frame_view.active_frame_index())
        self.label.text = f"Zoom: {int(self.frame_view.zoom_level.scale() * 100)}%"
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        if pyglet.window.key.MOD_CTRL & modifiers:
            if symbol == pyglet.window.key.X:
                coords = self.frame_view.crop_image_coordinates()
                if coords is not None:
                    t = self.frame_view.active_frame_index()
                    coords_dict = {
                        "t": [
                            t,
                            t + 1,
                        ],
                        "x": [coords.c1.x, coords.c2.x],
                        "y": [coords.c1.y, coords.c2.y],
                    }
                    print(f"Crop: {coords_dict}")
                    self.set_clipboard_text(str(coords_dict))
                else:
                    print("Nothing to crop - no selection")
            if symbol == pyglet.window.key.C:
                animation = self.frame_view.active_animation()
                coords = self.frame_view.crop_image_coordinates()
                has_selection = coords is not None and coords.crop_area() > 0
                if animation is not None and has_selection:
                    t = self.frame_view.active_frame_index()
                    image = animation.frames[
                        t, coords.c1.y : coords.c2.y, coords.c1.x : coords.c2.x
                    ]
                    io.copy_array_to_clipboard(image)
                else:
                    print("Nothing to copy - no selection")
            if symbol == pyglet.window.key.N:
                animation = self.frame_view.active_animation()
                coords = self.frame_view.crop_image_coordinates()
                has_selection = coords is not None and coords.crop_area() > 0
                if animation is not None and has_selection:
                    t = self.frame_view.active_frame_index()
                    # TODO: Allow selecting the end frame on the slider
                    t_end = min(t + 16, len(animation.frames))
                    data = animation.frames[
                        t:t_end, coords.c1.y : coords.c2.y, coords.c1.x : coords.c2.x
                    ]
                    np.save(
                        self.outputs_root
                        / f"crop_{t}-{t_end}_{coords.c1.x}-{coords.c2.x}_{coords.c1.y}-{coords.c2.y}.npy",
                        data,
                    )
                else:
                    print("Nothing to save - no selection")
            if symbol == pyglet.window.key.Q:
                self.close()
        if symbol == pyglet.window.key.ESCAPE:
            return pyglet.event.EVENT_HANDLED


def show_frame_sequences(
    frame_sequences: dict[str, FrameSequence],
    outputs_root: str | Path | None = None,
):
    viewer_window = ViewerWindow(outputs_root=outputs_root)
    viewer_window.add_animations(
        {
            name: FrameSequenceAnimation(sequence)
            for name, sequence in frame_sequences.items()
        }
    )

    pyglet.app.run()
    pyglet.app.exit()


def show_video_array(
    video_array, fps: float = 30, outputs_root: str | Path | None = None
):
    return show_frame_sequences(
        {"main": FrameSequence(video_array, fps=fps)},
        outputs_root=outputs_root,
    )
