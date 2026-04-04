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


class RenderGroup(Group):
    def __init__(self, order=0, parent=None):
        super().__init__(order, parent)
        self.program = ShaderProgram(
            Shader(shaders.load_shader("side_vignette_vertex.glsl"), "vertex"),
            Shader(shaders.load_shader("side_vignette_fragment.glsl"), "fragment"),
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


class SideVignette(EventDispatcher):
    """Fancy slider widget"""

    def __init__(
        self,
        width,
        height,
        batch: pyglet.graphics.Batch,
        parent_group: pyglet.graphics.Group,
        show_margin_ratio=0.2,
    ):
        self.width = width
        self.height = height
        # Fraction of width that triggers the vignette to show up
        self.show_margin = show_margin_ratio

        self.batch = batch

        self.group = RenderGroup(parent=parent_group)
        self.vertex_list = self.group.create_vertex_list(self.batch)

        self.is_hovered = False
        self.is_shift_held = False

    def on_mouse_motion(self, x, y, dx, dy):
        if self.is_in_show_boundary(x, y):
            self.is_hovered = True
        else:
            self.is_hovered = False

    def handle_keys(self, keys: pyglet.window.key.KeyStateHandler):
        if keys.data.get(pyglet.window.key.LSHIFT) or keys.data.get(
            pyglet.window.key.RSHIFT
        ):
            self.is_shift_held = True
        else:
            self.is_shift_held = False

    def update_geometry(self, width, height):
        self.width = width
        self.height = height

    def is_in_show_boundary(self, x, y):
        box_width = self.width * self.show_margin
        box_height = self.height
        is_x_in_boundary = 0 <= x <= box_width
        is_y_in_boundary = 0 <= y <= box_height
        return is_x_in_boundary and is_y_in_boundary

    def on_draw(self):
        box_width = self.width
        box_height = self.height

        visible = self.is_hovered or self.is_shift_held
        self.group.program["alpha"] = 1.0 if visible else 0.0
        self.group.program["scale"] = Vec2(box_width, box_height)
