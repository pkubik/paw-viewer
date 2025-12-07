import pyglet
from pyglet.event import EventDispatcher
from pyglet.gl import (
    GL_BLEND,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TRIANGLES,
    glBlendFunc,
    glDisable,
    glEnable,
)
from pyglet.graphics import Group
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.math import Vec2

from paw_viewer import shaders

_vertex_source = shaders.load_slider_vertex_shader()
_fragment_source = shaders.load_slider_fragment_shader()


class RenderGroup(Group):
    def __init__(self, order=0, parent=None):
        super().__init__(order, parent)
        self.program = ShaderProgram(
            Shader(_vertex_source, "vertex"),
            Shader(_fragment_source, "fragment"),
        )

    def set_state(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.program.use()

    def unset_state(self):
        glDisable(GL_BLEND)

    def create_vertex_list(self, batch):
        return self.program.vertex_list_indexed(
            4,
            GL_TRIANGLES,
            shaders.QUAD_INDICES,
            batch,
            self,
            position=("f", shaders.QUAD_CORNER_COORDS),
        )

    def __hash__(self):
        return hash(
            (
                self.order,
                self.parent,
                self.program,
            )
        )

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__
            and self.order == other.order
            and self.program == other.program
            and self.parent == other.parent
        )


def clip(x, min_x, max_x):
    return max(min(x, max_x), min_x)


class Slider(EventDispatcher):
    """Fancy slider widget"""

    def __init__(self, x, y, length, steps: int, batch: pyglet.graphics.Batch):
        self.x = x
        self.y = y
        self.length = length
        self.batch = batch
        self.stroke = 10
        self.current_step = 0
        self.total_steps = steps
        self.is_dragged = False

        self.group = RenderGroup(order=2)
        self.vertex_list = self.group.create_vertex_list(self.batch)
        self.slider_ubo = self.group.program.uniform_blocks["Slider"].create_ubo()

        self.register_event_type("on_change")

    def update_step(self, step: int):
        self.current_step = step

    def on_mouse_release(self, x, y, buttons, modifiers):
        self.is_dragged = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self.on_mouse_press(x + dx, y + dy, buttons, modifiers)

    def on_mouse_press(self, x, y, buttons, modifiers):
        box_width = self.length
        box_height = 2 * self.stroke
        is_in_box = (self.x <= x <= self.x + box_width) and (
            self.y <= y <= self.y + box_height
        )
        if (is_in_box or self.is_dragged) and buttons & pyglet.window.mouse.LEFT:
            self.is_dragged = True
            start_x = self.x + self.stroke
            end_x = self.x + self.length - self.stroke
            ratio = (x - start_x) / (end_x - start_x)
            self.current_step = clip(
                int(ratio * self.total_steps), 0, self.total_steps - 1
            )
            self.dispatch_event("on_change", self.current_step)
            return True

    def on_draw(self):
        box_width = self.length
        box_height = 2 * self.stroke
        inner_slider_length = self.length - 2 * self.stroke
        start_x = self.x + self.stroke
        end_x = self.x + box_width - self.stroke

        current_step = self.current_step
        total_steps = self.total_steps
        visible = start_x < end_x and total_steps > 1

        self.group.program["translation"] = Vec2(self.x, self.y)
        self.group.program["scale"] = (
            Vec2(box_width, box_height) if visible else Vec2(0, 0)
        )
        with self.slider_ubo as slider:
            slider.start_x = float(start_x)
            slider.end_x = float(end_x)
            slider.knob_x = float(
                start_x + inner_slider_length * (current_step + 1) / total_steps
            )
            slider.y = float(self.y + self.stroke)
            slider.steps = self.total_steps
