#version 420 core

in vec4 vertex_colors;
in vec2 coords;
out vec4 final_color;

void main()
{
    final_color = vec4(1, coords.x, coords.y, 1);
}
