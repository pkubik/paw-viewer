#version 420 core
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