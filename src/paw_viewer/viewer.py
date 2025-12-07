import numpy as np
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
from pyglet.math import Mat4, Vec2, Vec3

from paw_viewer import shaders
from paw_viewer.frame_sequence import FrameSequence
from paw_viewer.slider import Slider
from paw_viewer.zoom_level import ZoomLevel

_vertex_source = shaders.load_vertex_shader()
_fragment_source = shaders.load_fragment_shader()


class RenderGroup(Group):
    def __init__(self, texture, program, order=0, parent=None):
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
        self.program = program

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


class FrameView:
    """Handles the viewport for rendering frames."""

    def __init__(
        self, width, height, frame_sequence: FrameSequence, batch: pyglet.graphics.Batch
    ):
        self.width = width
        self.height = height
        self.frame_sequence = frame_sequence
        self.texture = frame_sequence.texture
        self.indices = shaders.QUAD_INDICES
        self.vertex_positions = shaders.create_quad_from_texture(self.texture)
        self.batch = batch

        # Initialize shaders
        self.vert_shader = Shader(_vertex_source, "vertex")
        self.frag_shader = Shader(_fragment_source, "fragment")
        self.shader_program = ShaderProgram(self.vert_shader, self.frag_shader)

        # Create render group
        self.group = RenderGroup(self.texture, self.shader_program, order=1)
        self.vertex_list = self.create_vertex_list()

        # Viewport state
        self.model = pyglet.math.Mat4()
        self.window_center = Vec3(width / 2, height / 2, 0)
        self.cursor_translation = Vec3(width / 2, height / 2, 0)
        self.translation = Vec3(width / 2, height / 2, 0)
        self.zoom_level = ZoomLevel()
        self.scroll_speed = 20  # in pixels

    def create_vertex_list(self):
        return self.shader_program.vertex_list_indexed(
            4,
            GL_TRIANGLES,
            self.indices,
            self.batch,
            self.group,
            position=("f", self.vertex_positions),
            tex_coords=("f", self.texture.tex_coords),
        )

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

        if keys.data.get(pyglet.window.key.LCTRL) and keys.data.get(
            pyglet.window.key.R
        ):
            self.zoom_level.reset()
            self.translation = Vec3(self.width / 2, self.height / 2, 0)

        scale = self.zoom_level.scale()
        self.model = Mat4().translate(self.translation).scale(Vec3(scale, scale, 1.0))
        self.shader_program["model"] = self.model


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
