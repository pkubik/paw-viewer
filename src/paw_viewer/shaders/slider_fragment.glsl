#version 420 core

in vec4 vertex_colors;
in vec2 coords;
in vec2 bottom_left;
in vec2 top_right;
out vec4 final_color;

uniform Bar
{
    float start_x;
    float end_x;
    float knob_x;
    float y;
} bar;

void main()
{
    vec2 v1 = vec2(bar.start_x, bar.y);
    vec2 v2 = vec2(bar.end_x, bar.y);

    float d = abs(gl_FragCoord.y - bar.y);
    if (gl_FragCoord.x < v1.x || gl_FragCoord.x > v2.x) {
        float d1 = length(gl_FragCoord.xy - v1);
        float d2 = length(gl_FragCoord.xy - v2);
        d = min(d1, d2);
    }

    float m1 = 1.0 - smoothstep(5., 10., d);
    float m2 = 1.0 - smoothstep(4., 5., d);
    m1 = clamp(m1 - m2, 0., 1.);
    final_color = mix(vec4(0), vec4(0.9, 0.9, 0.9, 0.9), m1) + mix(vec4(0), vec4(0.2, 0.5, 0.3, 0.8), m2);
}
