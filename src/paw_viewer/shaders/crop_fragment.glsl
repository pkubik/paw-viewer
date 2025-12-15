#version 420 core
out vec4 final_colors;

void main()
{
    final_colors = vec4(fract(gl_FragCoord.xy * 100.), 0., 0.5);
}
