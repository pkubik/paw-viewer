import pyglet
from pathlib import Path

pyglet.resource.path += [str(Path(__file__).parent)]


class Slider:
    def __init__(self, frame, min_value=0, max_value=100, initial_value=50, batch=None):
        bar = pyglet.resource.image("bar.png")
        knob = pyglet.resource.image("knob.png")
        bar.width = 700
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.slider = pyglet.gui.Slider(30, 20, bar, knob, edge=5, batch=batch)
        self.slider.set_handler("on_change", self.set_value)
        frame.add_widget(self.slider)
        self.label = pyglet.text.Label(
            "Slider Value: 0.0", x=10, y=20, batch=batch, color=(0, 0, 0, 255)
        )

    def set_value(self, slider, value):
        self.label.text = f"Slider Value: {value:.2f}"
        if self.min_value <= value <= self.max_value:
            self.value = value
        else:
            raise ValueError(
                f"Value {value} out of range [{self.min_value}, {self.max_value}]"
            )

    def handle_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.slider._check_hit(x, y):
            self.slider.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
            return True
        return False