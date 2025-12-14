#version 420 core
in vec2 position;
out vec4 image_position;

uniform WindowBlock
{ // This UBO is defined on Window creation, and available
    mat4 projection; // in all Shaders. You can modify these matrixes with the
    mat4 view; // Window.view and Window.projection properties.
} window;

uniform mat4 model;

vec2 CORNERS[4] = vec2[4](
        vec2(-1.0, -1.0),
        vec2(1.0, -1.0),
        vec2(1.0, 1.0),
        vec2(-1.0, 1.0)
    );

void main()
{
    image_position = window.projection * window.view * model * vec4(position, 1, 1);
    gl_Position = vec4(CORNERS[gl_VertexID], 0., 1.);
}
