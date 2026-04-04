import pyglet
from pyglet.event import EventDispatcher
import numpy as np

from paw_viewer.style import ACCENT_COLOR, FG_COLOR


class ScalarWidget(EventDispatcher):
    """
    Scalar widget with scroll and mouse-drag support.
    """

    def __init__(
        self,
        initial_value: float,
        value_step: float,
        window: pyglet.window.BaseWindow,
        batch: pyglet.graphics.Batch,
        group: pyglet.graphics.Group = None,
        min_value: float = -np.inf,
        padding: int = 4,
        font_size: int = 16,
        format_string: str = "{}",
    ):
        self.initial_value = initial_value
        self.value = initial_value
        self.format_string = format_string
        self.padding = padding
        self.window = window
        self.value_step = value_step
        self.min_value = min_value

        self.label = pyglet.text.Label(
            self.format_string.format(self.value),
            x=0,
            y=0,
            font_size=font_size,
            font_name="Lucida Console",
            batch=batch,
            group=group,
        )

        self.is_dragged = False
        self.register_event_type("on_change")

    def update_geometry(self, x, y):
        self.label.x = x + self.padding
        self.label.y = y + self.padding

    def update_label(self):
        self.label.text = self.format_string.format(self.value)

    def on_mouse_release(self, x, y, buttons, modifiers):
        self.is_dragged = False
        self.window.set_exclusive_mouse(False)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if self.is_in_boundary(x, y):
            if buttons & pyglet.window.mouse.LEFT:
                self.is_dragged = True
                self.window.set_exclusive_mouse(True)
                return True
            elif buttons & pyglet.window.mouse.RIGHT:
                self.value = self.initial_value
                self.trigger_change()
                return True
        return False

    def on_mouse_motion(self, x, y, dx, dy):
        if self.is_dragged or self.is_in_boundary(x, y):
            self.label.color = ACCENT_COLOR

        else:
            self.label.color = FG_COLOR

        if self.is_dragged:
            d = dx + dy
            self.value += round(np.sign(d) * np.abs(d) ** 2) * self.value_step
            self.value = max(self.value, self.min_value)
            self.trigger_change()
            return True

    def is_in_boundary(self, x, y):
        box_x1 = self.label.x - self.padding
        box_x2 = self.label.right + self.padding
        box_y1 = self.label.y - self.padding
        box_y2 = self.label.top + self.padding
        is_x_in_boundary = box_x1 <= x <= box_x2
        is_y_in_boundary = box_y1 <= y <= box_y2
        return is_x_in_boundary and is_y_in_boundary

    def trigger_change(self):
        self.update_label()
        self.dispatch_event("on_change", self.value)
