#version 420 core

in vec2 coords;
out vec4 final_color;
uniform float alpha;

void main()
{
    float pos = max(0.0, coords.x);
    float mask = alpha * smoothstep(1.0, 0.6, pos);
    final_color = vec4(0.0, 0.0, 0.0, mask);
}
