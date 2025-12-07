#version 420 core
in vec2 position;
out vec2 coords;
out vec2 bottom_left;
out vec2 top_right;

uniform WindowBlock
{                       // This UBO is defined on Window creation, and available
    mat4 projection;    // in all Shaders. You can modify these matrixes with the
    mat4 view;          // Window.view and Window.projection properties.
} window;

uniform vec2 translation;
uniform vec2 scale;

void main()
{
    gl_Position = window.projection * window.view * vec4(scale * position + translation, 1, 1);
    coords = position;
    bottom_left = translation;
    top_right = translation + scale;
}
