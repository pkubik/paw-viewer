import pyglet
import numpy as np

from pyglet.gl import (
    glActiveTexture,
    glBindTexture,
    glEnable,
    glBlendFunc,
    glDisable,
    glTexParameteri,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_NEAREST,
    GL_TEXTURE0,
    GL_TRIANGLES,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
)
from pyglet.math import Mat4, Vec2, Vec3
from pyglet.graphics import Group
from pyglet.graphics.shader import Shader, ShaderProgram
from paw_viewer import shaders

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


def create_quad(x, y, texture):
    x1 = -texture.width / 2 + x
    y1 = -texture.height / 2 + y
    x2 = texture.width / 2 + x
    y2 = texture.height / 2 + y
    return x1, y1, x2, y1, x2, y2, x1, y2


class ZoomLevel:
    def __init__(self, min_log_scale: float = -8.0, max_log_scale: float = 8.0):
        self.log_scale = 0.0
        self.min_log_scale = min_log_scale
        self.max_log_scale = max_log_scale

    def scale(self) -> float:
        return 2**self.log_scale

    def zoom_in(self, increment: float = 0.25) -> float:
        current_scale = self.scale()
        self.log_scale = min(self.log_scale + increment, self.max_log_scale)
        new_scale = self.scale()
        return new_scale / current_scale

    def zoom_out(self, decrement: float = 0.25) -> float:
        return self.zoom_in(-decrement)

    def reset(self):
        self.log_scale = 0.0


class FrameSequence:
    """Represents a sequence of frames (images) and the texture used for rendering them."""

    def __init__(self, frames: np.ndarray, fps: float = 30):
        self.frames = frames
        self.fps = fps
        self.num_frames = frames.shape[0]
        self.frame_index = 0
        self.running = False

        image = self.frames[0]
        self.image_data = pyglet.image.ImageData(
            width=image.shape[1],
            height=image.shape[0],
            fmt="RGB",
            data=image.tobytes(),
            pitch=-image.shape[1] * 3,
        )
        self.texture = self.image_data.get_texture()

    def animation_step(self, dt):
        if not self.running:
            # just in case - this should not be called when not running
            return
        self.frame_index = (self.frame_index + 1) % self.num_frames
        self.update_texture()

    def update_texture(self):
        image = self.frames[self.frame_index]
        self.image_data.set_data(
            fmt="RGB",
            pitch=-image.shape[1] * 3,
            data=image.tobytes(),
        )
        self.texture.blit_into(self.image_data, 0, 0, 0)

    def start(self):
        pyglet.clock.schedule_interval(self.animation_step, 1 / self.fps)
        self.running = True

    def stop(self):
        pyglet.clock.unschedule(self.animation_step)
        self.running = False

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def go_start(self):
        self.frame_index = 0
        self.update_texture()

    def go_end(self):
        self.frame_index = self.num_frames - 1
        self.update_texture()

    def go_next(self):
        self.frame_index = (self.frame_index + 1) % self.num_frames
        self.update_texture()

    def go_previous(self):
        self.frame_index = (self.frame_index - 1) % self.num_frames
        self.update_texture()


class FrameView:
    """Handles the viewport for rendering frames."""

    def __init__(self, frame_sequence: FrameSequence, batch: pyglet.graphics.Batch):
        self.frame_sequence = frame_sequence
        self.texture = frame_sequence.texture
        self.indices = (0, 1, 2, 0, 2, 3)
        self.vertex_positions = create_quad(0, 0, self.texture)
        self.batch = batch

        # Initialize shaders
        self.vert_shader = Shader(_vertex_source, "vertex")
        self.frag_shader = Shader(_fragment_source, "fragment")
        self.shader_program = ShaderProgram(self.vert_shader, self.frag_shader)

        # Create render group
        self.group = RenderGroup(self.texture, self.shader_program)
        self.vertex_list = self.create_vertex_list(self.batch)

    def update_model(self, model: Mat4):
        self.shader_program["model"] = model

    def create_vertex_list(self, batch: pyglet.graphics.Batch):
        return self.shader_program.vertex_list_indexed(
            4,
            GL_TRIANGLES,
            self.indices,
            batch,
            self.group,
            position=("f", self.vertex_positions),
            tex_coords=("f", self.texture.tex_coords),
        )


class ViewerWindow(pyglet.window.Window):
    def __init__(self, frame_sequence: FrameSequence, **kwargs):
        super().__init__(**kwargs)
        self.frame_sequence = frame_sequence

        self.batch = pyglet.graphics.Batch()
        self.model = pyglet.math.Mat4()
        self.window_center = Vec3(self.width / 2, self.height / 2, 0)
        self.cursor_translation = Vec3(self.width / 2, self.height / 2, 0)
        self.translation = Vec3(self.width / 2, self.height / 2, 0)
        self.zoom_level = ZoomLevel()
        self.scroll_speed = 20  # in pixels
        pyglet.gl.glClearColor(0.05, 0.08, 0.06, 1)
        self.label = pyglet.text.Label("Zoom: 100%", x=5, y=5, batch=self.batch)

        self.key_state = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_state)

        self.frame_view = FrameView(frame_sequence, batch=self.batch)

    def on_mouse_motion(self, x, y, dx, dy):
        self.cursor_translation = Vec3(x, y, 0)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.translation += Vec3(dx, dy, 0)

    def on_resize(self, width, height):
        new_window_center = Vec3(width / 2, height / 2, 0)
        center_offset = new_window_center - self.window_center
        self.window_center = new_window_center
        self.translation += Vec3(center_offset.x, center_offset.y, 0)

    def on_draw(self):
        keys = self.key_state
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
        self.label.text = f"Zoom: {int(scale * 100)}%"

        self.frame_view.update_model(self.model)
        self.clear()
        self.batch.draw()

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
            if symbol == pyglet.window.key.Q:
                self.close()
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
        if symbol == pyglet.window.key.ESCAPE:
            return pyglet.event.EVENT_HANDLED


def show_video_array(video_array, fps: float = 30):
    frame_sequence = FrameSequence(video_array, fps=fps)
    viewer_window = ViewerWindow(frame_sequence=frame_sequence)

    pyglet.app.run()
