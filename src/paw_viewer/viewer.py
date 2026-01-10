import os
from pathlib import Path

import numpy as np
import pyglet

from paw_viewer import io
from paw_viewer.animation import Animation
from paw_viewer.frame_view import FrameView
from paw_viewer.slider import Slider


class ViewerWindow(pyglet.window.Window):
    def __init__(
        self,
        animation: Animation,
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

        self.animation = animation
        self.key_state = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_state)

        self.frame_view = FrameView(
            self.width,
            self.height,
            self.animation,
            batch=self.batch,
        )
        self.push_handlers(self.frame_view)

        @self.frame_view.event
        def on_source_change(source):
            self.update_source_labels()

        self.slider_margin = 200
        self.slider = Slider(
            x=self.slider_margin,
            y=20,
            length=self.width - 2 * self.slider_margin,
            steps=self.animation.num_frames,
            batch=self.batch,
            parent_group=self.overlay_group,
        )
        self.push_handlers(self.slider)

        @self.slider.event
        def on_change(value):
            self.animation.frame_index = value

        self.label = pyglet.text.Label(
            "Zoom: 100%",
            x=16,
            y=16,
            font_size=16,
            font_name="Lucida Console",
            batch=self.batch,
            group=self.overlay_group,
        )

        if len(self.animation.names) > 1:
            self.source_labels = [
                pyglet.text.Label(
                    f"{i + 1:>4}. {name}",
                    x=5,
                    y=500,
                    font_size=14,
                    font_name="Lucida Console",
                    batch=self.batch,
                    group=self.overlay_group,
                    anchor_x="left",
                )
                for i, name in enumerate(self.animation.names)
            ]
            self.update_source_labels()
        else:
            self.source_labels = []

        self.invalid = False

    def update_source_labels(self) -> None:
        for i, label in enumerate(self.source_labels):
            index = i - self.animation.active_source
            label.y = self.height // 2 - index * 20
            if i == self.animation.active_source:
                label.color = (20, 200, 50, 200)
                label.weight = "bold"
                label.x = 16
                label.font_size = 14
            else:
                label.color = (110, 140, 120, 150)
                label.weight = "normal"
                label.x = 8
                label.font_size = 12

    def on_resize(self, width: int, height: int):
        if self.invalid:
            # For some reason this event is triggered for uninitialized window,
            # that is being created after closing a previous one
            return super().on_resize(width, height)
        self.slider.length = self.width - 2 * self.slider_margin
        self.slider.update_geometry()
        self.update_source_labels()
        return super().on_resize(width, height)

    def on_draw(self):
        self.frame_view.handle_keys(self.key_state)
        self.slider.update_step(self.animation.frame_index)
        self.label.text = f"Zoom: {int(self.frame_view.zoom_level.scale() * 100)}%"
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        if pyglet.window.key.MOD_CTRL & modifiers:
            if symbol == pyglet.window.key.X:
                coords = self.frame_view.crop_image_coordinates()
                if coords is not None:
                    coords_dict = {
                        "source": self.animation.active_source_name(),
                        "t": [
                            self.animation.frame_index,
                            self.animation.frame_index + 1,
                        ],
                        "x": [coords.c1.x, coords.c2.x],
                        "y": [coords.c1.y, coords.c2.y],
                    }
                    print(f"Crop: {coords_dict}")
                    self.set_clipboard_text(str(coords_dict))
                else:
                    print("Nothing to crop - no selection")
            if symbol == pyglet.window.key.C:
                coords = self.frame_view.crop_image_coordinates()
                if coords is not None and coords.crop_area() > 0:
                    frame = self.animation.frame_as_uint8()
                    image = frame[coords.c1.y : coords.c2.y, coords.c1.x : coords.c2.x]
                    io.copy_array_to_clipboard(image)
                else:
                    print("Nothing to copy - no selection")
            if symbol == pyglet.window.key.N:
                coords = self.frame_view.crop_image_coordinates()
                if coords is not None and coords.crop_area() > 0:
                    t = self.animation.frame_index
                    # TODO: Allow selecting the end frame on the slider
                    t_end = min(t + 16, len(self.animation.frames))
                    data = self.animation.frames[
                        t:t_end, coords.c1.y : coords.c2.y, coords.c1.x : coords.c2.x
                    ]
                    source_name = self.animation.active_source_name()
                    output_path = (
                        self.outputs_root
                        / f"crop_{source_name}_{t}-{t_end}_{coords.c1.x}-{coords.c2.x}_{coords.c1.y}-{coords.c2.y}.npy"
                    )
                    np.save(
                        output_path,
                        data,
                    )
                    print(f"Saved crop npy as {output_path}")
                else:
                    print("Nothing to save - no selection")
            if symbol == pyglet.window.key.Q:
                self.close()
        if symbol == pyglet.window.key.ESCAPE:
            return pyglet.event.EVENT_HANDLED


def show_video_arrays(
    video_arrays: dict[str, np.ndarray],
    fps: float = 30,
    outputs_root: str | Path | None = None,
):
    animation = Animation(
        # "neg" just for reference now
        video_arrays,
        fps=fps,
    )
    viewer_window = ViewerWindow(animation=animation, outputs_root=outputs_root)

    pyglet.app.run()
    pyglet.app.exit()


def show_video_array(
    video_array, fps: float = 30, outputs_root: str | Path | None = None
):
    show_video_arrays({"": video_array})
