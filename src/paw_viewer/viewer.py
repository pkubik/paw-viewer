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

_vertex_source = """#version 420 core
    in vec2 position;
    in vec3 tex_coords;
    out vec3 texture_coords;

    uniform WindowBlock
    {                       // This UBO is defined on Window creation, and available
        mat4 projection;    // in all Shaders. You can modify these matrixes with the
        mat4 view;          // Window.view and Window.projection properties.
    } window;

    uniform mat4 model;

    void main()
    {
        gl_Position = window.projection * window.view * model * vec4(position, 1, 1);
        texture_coords = tex_coords;
    }
"""

_fragment_source = """#version 420 core
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        final_colors = texture(our_texture, texture_coords.xy);
    }
"""

vert_shader = Shader(_vertex_source, "vertex")
frag_shader = Shader(_fragment_source, "fragment")
shader_program = ShaderProgram(vert_shader, frag_shader)


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
        self.group = RenderGroup(self.texture, shader_program)
        self.indices = (0, 1, 2, 0, 2, 3)

        self.vertex_positions = create_quad(0, 0, self.texture)

    def create_vertex_list(self, batch: pyglet.graphics.Batch):
        return shader_program.vertex_list_indexed(
            4,
            GL_TRIANGLES,
            self.indices,
            batch,
            self.group,
            position=("f", self.vertex_positions),
            tex_coords=("f", self.texture.tex_coords),
        )

    def animation_step(self, dt):
        if not self.running:
            # just in case - this should not be called when not running
            return
        self.frame_index = (self.frame_index + 1) % self.num_frames
        self.update_texture()

    def update_texture(self):
        """
        Scheduled function to update the texture content efficiently.
        """
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


def show_video_array(video_array, fps: float = 30):
    frame_sequence = FrameSequence(video_array, fps)

    window = pyglet.window.Window(resizable=True)
    batch = pyglet.graphics.Batch()
    model = pyglet.math.Mat4()
    window_center = Vec3(window.width / 2, window.height / 2, 0)
    cursor_translation = Vec3(window.width / 2, window.height / 2, 0)
    translation = Vec3(window.width / 2, window.height / 2, 0)
    zoom_level = ZoomLevel()
    scroll_speed = 20  # in pixels

    pyglet.gl.glClearColor(0.05, 0.08, 0.06, 1)
    label = pyglet.text.Label("Zoom: 100%", x=5, y=5, batch=batch)

    keys = pyglet.window.key.KeyStateHandler()

    @window.event
    def on_mouse_motion(x, y, dx, dy):
        nonlocal cursor_translation
        cursor_translation = Vec3(x, y, 0)

    @window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            nonlocal translation
            translation += Vec3(dx, dy, 0)

    @window.event
    def on_resize(width, height):
        nonlocal translation
        nonlocal window_center
        new_window_center = Vec3(width / 2, height / 2, 0)
        center_offset = new_window_center - window_center
        window_center = new_window_center
        translation += Vec3(center_offset.x, center_offset.y, 0)

    @window.event
    def on_draw():
        nonlocal model
        nonlocal translation
        nonlocal zoom_level

        if not keys.data.get(pyglet.window.key.LCTRL):
            if keys.data.get(pyglet.window.key.W):
                translation += Vec3(0, -scroll_speed, 0)
            if keys.data.get(pyglet.window.key.S):
                translation += Vec3(0, scroll_speed, 0)
            if keys.data.get(pyglet.window.key.A):
                translation += Vec3(scroll_speed, 0, 0)
            if keys.data.get(pyglet.window.key.D):
                translation += Vec3(-scroll_speed, 0, 0)
            if keys.data.get(pyglet.window.key.R):
                scale_factor = zoom_level.zoom_in(0.25)
                translation = (
                    translation - cursor_translation
                ) * scale_factor + cursor_translation
            if keys.data.get(pyglet.window.key.F):
                scale_factor = zoom_level.zoom_out(0.25)
                translation = (
                    translation - cursor_translation
                ) * scale_factor + cursor_translation

        if keys.data.get(pyglet.window.key.LCTRL) and keys.data.get(
            pyglet.window.key.R
        ):
            zoom_level.reset()
            translation = Vec3(window.width / 2, window.height / 2, 0)

        scale = zoom_level.scale()
        model = Mat4().translate(translation).scale(Vec3(scale, scale, 1.0))

        label.text = f"Zoom: {int(scale * 100)}%"

        shader_program["model"] = model
        window.clear()
        batch.draw()

    @window.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        nonlocal translation
        nonlocal zoom_level

        if scroll_y > 0:
            scale_factor = zoom_level.zoom_in(0.5 * scroll_y)
            translation = (
                translation - cursor_translation
            ) * scale_factor + cursor_translation
        elif scroll_y < 0:
            scale_factor = zoom_level.zoom_out(-0.5 * scroll_y)
            translation = (
                translation - cursor_translation
            ) * scale_factor + cursor_translation

    @window.event
    def on_key_press(symbol, modifiers):
        if pyglet.window.key.MOD_CTRL & modifiers:
            if symbol == pyglet.window.key.Q:
                window.close()
            if symbol == pyglet.window.key.S:
                frame_sequence.go_start()
            if symbol == pyglet.window.key.D:
                frame_sequence.go_next()
            if symbol == pyglet.window.key.A:
                frame_sequence.go_previous()
            if symbol == pyglet.window.key.E:
                frame_sequence.go_end()
        if symbol == pyglet.window.key.SPACE:
            frame_sequence.toggle()
        if symbol == pyglet.window.key.ESCAPE:
            return pyglet.event.EVENT_HANDLED

    vertex_list = frame_sequence.create_vertex_list(batch)

    window.push_handlers(keys)
    pyglet.app.run()
