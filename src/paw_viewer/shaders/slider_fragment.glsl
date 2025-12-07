#version 420 core

in vec4 vertex_colors;
in vec2 coords;
in vec2 bottom_left;
in vec2 top_right;
in float x1;
in float x2;
in float y;
out vec4 final_color;

void main()
{
    float d = abs(gl_FragCoord.y - y);
    if (gl_FragCoord.x < x1 || gl_FragCoord.x > x2) {
        float d1 = length(gl_FragCoord.xy - vec2(x1, y));
        float d2 = length(gl_FragCoord.xy - vec2(x2, y));
        d = min(d1, d2);
    }

    float m1 = 1.0 - smoothstep(5., 10., d);
    float m2 = 1.0 - smoothstep(4., 5., d);
    m1 = clamp(m1 - m2, 0., 1.);
    final_color = mix(vec4(0), vec4(0.9, 0.9, 0.9, 0.9), m1) + mix(vec4(0), vec4(0.2, 0.5, 0.3, 0.8), m2);
}
