from dataclasses import dataclass

import pyglet
from pyglet.gl import (
    GL_BLEND,
    GL_NEAREST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE0,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TRIANGLES,
    glActiveTexture,
    glBindTexture,
    glBlendFunc,
    glDisable,
    glEnable,
    glTexParameteri,
)
from pyglet.graphics import Group
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.math import Mat4, Vec2, Vec3, Vec4

from paw_viewer import shaders
from paw_viewer.frame_sequence import FrameSequence
from paw_viewer.zoom_level import ZoomLevel


class RenderGroup(Group):
    def __init__(self, texture, order=0, parent=None):
        """Create a RenderGroup.

        :Parameters:
            `texture` : `~pyglet.image.Texture`
                Texture to bind.
            `program` : `~pyglet.graphics.shader.ShaderProgram`
                ShaderProgram to use.
            `order` : int
                Change the order to render above or below other Groups.
            `parent` : `~pyglet.graphics.Group`
                Parent group.
        """
        super().__init__(order, parent)
        self.texture = texture
        self.vert_shader = Shader(shaders.load_shader("vertex.glsl"), "vertex")
        self.frag_shader = Shader(shaders.load_shader("fragment.glsl"), "fragment")
        self.program = ShaderProgram(self.vert_shader, self.frag_shader)

    def create_vertex_list(self, batch):
        return self.program.vertex_list_indexed(
            4,
            GL_TRIANGLES,
            shaders.QUAD_INDICES,
            batch,
            self,
            position=("f", shaders.create_quad_from_texture(self.texture)),
            tex_coords=("f", self.texture.tex_coords),
        )

    def set_state(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)
        glTexParameteri(self.texture.target, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(self.texture.target, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.program.use()

    def unset_state(self):
        glDisable(GL_BLEND)

    def __hash__(self):
        return hash(
            (
                self.texture.target,
                self.texture.id,
                self.order,
                self.parent,
                self.program,
            )
        )

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__
            and self.texture.target == other.texture.target
            and self.texture.id == other.texture.id
            and self.order == other.order
            and self.program == other.program
            and self.parent == other.parent
        )


class BackgroundRenderGroup(Group):
    def __init__(self, order=0, parent=None):
        super().__init__(order, parent)
        self.program = ShaderProgram(
            Shader(shaders.load_shader("background_vertex.glsl"), "vertex"),
            Shader(shaders.load_shader("background_fragment.glsl"), "fragment"),
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


@dataclass
class CropCorners:
    c1: Vec2 = Vec2()
    c2: Vec2 = Vec2()

    def crop_area(self):
        width = abs(self.c1.x - self.c2.x)
        height = abs(self.c1.y - self.c2.y)
        return width * height


class FrameView:
    """Handles the viewport for rendering frames."""

    def __init__(
        self, width, height, frame_sequence: FrameSequence, batch: pyglet.graphics.Batch
    ):
        self.width = width
        self.height = height
        self.frame_sequence = frame_sequence
        self.texture = frame_sequence.texture
        self.batch = batch

        # Create render groups
        self.bg_group = BackgroundRenderGroup(order=0)
        self.bg_vertex_list = self.bg_group.create_vertex_list(self.batch)

        self.group = RenderGroup(self.texture, order=4)
        self.vertex_list = self.group.create_vertex_list(self.batch)

        # Viewport state
        self.model = pyglet.math.Mat4()
        self.window_center = Vec3(width / 2, height / 2, 0)
        self.cursor_translation = Vec3(width / 2, height / 2, 0)
        self.translation = Vec3(width / 2, height / 2, 0)
        self.zoom_level = ZoomLevel()
        self.scroll_speed = 20  # in pixels
        self.crop_corners: CropCorners | None = None

    def crop_image_coordinates(self, invert_y=True):
        if self.crop_corners is None:
            return None

        offset = Vec2(self.group.texture.width // 2, self.group.texture.height // 2)
        c1 = self.crop_corners.c1 + offset
        c2 = self.crop_corners.c2 + offset

        x1 = min(c1.x, c2.x)
        x2 = max(c1.x, c2.x)
        y1 = min(c1.y, c2.y)
        y2 = max(c1.y, c2.y)

        if invert_y:
            # Both subtract from height and swap places to ensure that y2 is larger
            y1, y2 = self.group.texture.height - y2, self.group.texture.height - y1

        return CropCorners(Vec2(x1, y1), Vec2(x2, y2))

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        new_window_center = Vec3(width / 2, height / 2, 0)
        center_offset = new_window_center - self.window_center
        self.window_center = new_window_center
        self.translation += Vec3(center_offset.x, center_offset.y, 0)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.translation += Vec3(dx, dy, 0)

        if buttons & pyglet.window.mouse.RIGHT:
            max_xy = Vec2(self.group.texture.width // 2, self.group.texture.height // 2)
            min_xy = -max_xy

            if self.crop_corners is None:
                c1 = ~self.model @ Vec4(x, y, 0.0, 1.0)
                self.crop_corners = CropCorners()
                # TODO: Make sure the rounding is pixel-perfect even for odd texture sizes
                self.crop_corners.c1 = Vec2(round(c1.x), round(c1.y)).clamp(
                    min_xy, max_xy
                )

            c2 = ~self.model @ Vec4(x + dx, y + dy, 0.0, 1.0)
            self.crop_corners.c2 = Vec2(round(c2.x), round(c2.y)).clamp(min_xy, max_xy)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & pyglet.window.mouse.RIGHT:
            self.crop_corners = None

    def on_mouse_motion(self, x, y, dx, dy):
        self.cursor_translation = Vec3(x, y, 0)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y > 0:
            scale_factor = self.zoom_level.zoom_in(0.5 * scroll_y)
            self.translation = (
                self.translation - self.cursor_translation
            ) * scale_factor + self.cursor_translation
        elif scroll_y < 0:
            scale_factor = self.zoom_level.zoom_out(-0.5 * scroll_y)
            self.translation = (
                self.translation - self.cursor_translation
            ) * scale_factor + self.cursor_translation

    def on_key_press(self, symbol, modifiers):
        if pyglet.window.key.MOD_CTRL & modifiers:
            if symbol == pyglet.window.key.S:
                self.frame_sequence.go_start()
            if symbol == pyglet.window.key.D:
                self.frame_sequence.go_next()
            if symbol == pyglet.window.key.A:
                self.frame_sequence.go_previous()
            if symbol == pyglet.window.key.E:
                self.frame_sequence.go_end()
        else:
            if symbol == pyglet.window.key.X:
                self.frame_sequence.next_source()
            if symbol == pyglet.window.key.Z:
                self.frame_sequence.previous_source()

        if symbol == pyglet.window.key.SPACE:
            self.frame_sequence.toggle()

    def handle_keys(self, keys: pyglet.window.key.KeyStateHandler):
        if not keys.data.get(pyglet.window.key.LCTRL):
            if keys.data.get(pyglet.window.key.W):
                self.translation += Vec3(0, -self.scroll_speed, 0)
            if keys.data.get(pyglet.window.key.S):
                self.translation += Vec3(0, self.scroll_speed, 0)
            if keys.data.get(pyglet.window.key.A):
                self.translation += Vec3(self.scroll_speed, 0, 0)
            if keys.data.get(pyglet.window.key.D):
                self.translation += Vec3(-self.scroll_speed, 0, 0)
            if keys.data.get(pyglet.window.key.R):
                scale_factor = self.zoom_level.zoom_in(0.25)
                self.translation = (
                    self.translation - self.cursor_translation
                ) * scale_factor + self.cursor_translation
            if keys.data.get(pyglet.window.key.F):
                scale_factor = self.zoom_level.zoom_out(0.25)
                self.translation = (
                    self.translation - self.cursor_translation
                ) * scale_factor + self.cursor_translation

        if keys.data.get(pyglet.window.key.LCTRL):
            if keys.data.get(pyglet.window.key.R):
                self.zoom_level.reset()
                self.translation = Vec3(self.width / 2, self.height / 2, 0)

        scale = self.zoom_level.scale()
        self.model = Mat4().translate(self.translation).scale(Vec3(scale, scale, 1.0))
        self.group.program["model"] = self.model

        crop = self.crop_corners or CropCorners()
        x1 = crop.c1.x
        y1 = crop.c1.y
        x2 = crop.c2.x
        y2 = crop.c2.y
        self.group.program["crop_corners"] = Vec4(x1, y1, x2, y2)
