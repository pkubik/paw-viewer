import pyglet
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


class Slider:
    """Fancy slider widget"""

    def __init__(self, x, y, width, height, batch: pyglet.graphics.Batch):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.batch = batch

        # Create render group
        self.group = RenderGroup(order=2)
        self.vertex_list = self.group.create_vertex_list(self.batch)

    def on_draw(self):
        self.group.program["translation"] = Vec2(self.x, self.y)
        self.group.program["scale"] = Vec2(self.width, self.height)
