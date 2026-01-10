from dataclasses import dataclass

import pyglet
from pyglet.event import EventDispatcher
from pyglet.gl import (
    GL_BLEND,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE0,
    GL_TRIANGLES,
    glActiveTexture,
    glBindTexture,
    glBlendFunc,
    glDisable,
    glEnable,
)
from pyglet.graphics import Group
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.math import Mat4, Vec2, Vec3, Vec4

from paw_viewer import shaders
from paw_viewer.animation import Animation
from paw_viewer.zoom_level import ZoomLevel


class RenderGroup(Group):
    def __init__(self, animation: Animation, order=0, parent=None):
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
        self.animation = animation
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
            position=(
                "f",
                shaders.create_quad_from_texture(self.animation.active_texture),
            ),
            tex_coords=("f", self.animation.active_texture.tex_coords),
        )

    def set_state(self):
        texture = self.animation.active_texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(texture.target, texture.id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.program.use()

    def unset_state(self):
        glDisable(GL_BLEND)

    def __hash__(self):
        return hash(
            (
                id(self.animation),
                self.order,
                self.parent,
                self.program,
            )
        )

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__
            and id(self.animation) == id(other.animation)
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


class FrameView(EventDispatcher):
    """Handles the viewport for rendering frames."""

    def __init__(
        self, width, height, animation: Animation, batch: pyglet.graphics.Batch
    ):
        self.width = width
        self.height = height
        self.animation = animation
        self.batch = batch

        # Create render groups
        self.bg_group = BackgroundRenderGroup(order=0)
        self.bg_vertex_list = self.bg_group.create_vertex_list(self.batch)

        self.group = RenderGroup(self.animation, order=4)
        self.vertex_list = self.group.create_vertex_list(self.batch)

        # Viewport state
        self.model = pyglet.math.Mat4()
        self.window_center = Vec3(width / 2, height / 2, 0)
        self.cursor_translation = Vec3(width / 2, height / 2, 0)
        self.translation = Vec3(width / 2, height / 2, 0)
        self.zoom_level = ZoomLevel()
        self.scroll_speed = 20  # in pixels
        self.crop_corners: CropCorners | None = None

        self.register_event_type("on_source_change")

    def crop_image_coordinates(self, invert_y=True):
        if self.crop_corners is None:
            return None

        texture = self.animation.active_texture
        c1 = self.crop_corners.c1
        c2 = self.crop_corners.c2

        x1 = min(c1.x, c2.x)
        x2 = max(c1.x, c2.x)
        y1 = min(c1.y, c2.y)
        y2 = max(c1.y, c2.y)

        if invert_y:
            # Both subtract from height and swap places to ensure that y2 is larger
            y1, y2 = texture.height - y2, texture.height - y1

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
            texture = self.animation.active_texture
            offset = Vec2(texture.width / 2, texture.height / 2)
            size = Vec2(texture.width, texture.height)

            if self.crop_corners is None:
                offset_c1 = ~self.model @ Vec4(x, y, 0.0, 1.0)
                c1 = Vec2(offset_c1.x, offset_c1.y) + offset

                self.crop_corners = CropCorners()
                self.crop_corners.c1 = Vec2(round(c1.x), round(c1.y)).clamp(
                    Vec2(0, 0), size
                )

            offset_c2 = ~self.model @ Vec4(x + dx, y + dy, 0.0, 1.0)
            c2 = Vec2(offset_c2.x, offset_c2.y) + offset
            self.crop_corners.c2 = Vec2(round(c2.x), round(c2.y)).clamp(
                Vec2(0, 0), size
            )
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
                self.animation.go_start()
            if symbol == pyglet.window.key.D:
                self.animation.go_next()
            if symbol == pyglet.window.key.A:
                self.animation.go_previous()
            if symbol == pyglet.window.key.E:
                self.animation.go_end()
        else:
            if symbol == pyglet.window.key.X:
                self.animation.next_source()
                self.dispatch_event("on_source_change", self.animation.active_source)
            if symbol == pyglet.window.key.Z:
                self.animation.previous_source()
                self.dispatch_event("on_source_change", self.animation.active_source)

        if symbol == pyglet.window.key.SPACE:
            self.animation.toggle()

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
        texture = self.animation.active_texture
        offset = Vec2(
            texture.width / 2,
            texture.height / 2,
        )
        c1 = crop.c1 - offset
        c2 = crop.c2 - offset
        x1 = c1.x
        y1 = c1.y
        x2 = c2.x
        y2 = c2.y
        self.group.program["crop_corners"] = Vec4(x1, y1, x2, y2)
