#version 420 core
in vec2 position;
in vec3 tex_coords;
out vec3 texture_coords;
out vec4 frag_crop_corners;
out vec2 frag_position;

uniform WindowBlock
{ // This UBO is defined on Window creation, and available
    mat4 projection; // in all Shaders. You can modify these matrixes with the
    mat4 view; // Window.view and Window.projection properties.
} window;

uniform mat4 model;
uniform vec4 crop_corners;

void main()
{
    gl_Position = window.projection * window.view * model * vec4(position, 1, 1);
    frag_position = gl_Position.xy;
    texture_coords = tex_coords;

    // Transform crop corners
    vec4 cc1 = window.projection * window.view * model * vec4(crop_corners.xy, 0., 1.);
    vec4 cc2 = window.projection * window.view * model * vec4(crop_corners.zw, 0., 1.);
    frag_crop_corners = vec4(cc1.xy, cc2.xy);
}
