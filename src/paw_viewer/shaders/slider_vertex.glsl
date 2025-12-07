#version 420 core
in vec2 position;
out vec2 coords;
out vec2 bottom_left;
out vec2 top_right;
out float x1;
out float x2;
out float y;

uniform WindowBlock
{                       // This UBO is defined on Window creation, and available
    mat4 projection;    // in all Shaders. You can modify these matrixes with the
    mat4 view;          // Window.view and Window.projection properties.
} window;

uniform vec2 translation;
uniform vec2 scale;
uniform vec2 v1;
uniform vec2 v2;

void main()
{
    gl_Position = window.projection * window.view * vec4(scale * position + translation, 1, 1);
    coords = position;
    bottom_left = translation;
    top_right = translation + scale;
    x1 = v1.x;
    x2 = v2.x;
    y = v2.y;
}
