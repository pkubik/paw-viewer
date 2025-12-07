#version 420 core

in vec4 vertex_colors;
in vec2 coords;
in vec2 bottom_left;
in vec2 top_right;
out vec4 final_color;

uniform Slider
{
    float start_x;
    float end_x;
    float knob_x;
    float y;
} slider;

float verticalBarSDF(vec2 v1, vec2 v2)
{
    float d = abs(gl_FragCoord.y - slider.y);
    if (gl_FragCoord.x < v1.x || gl_FragCoord.x > v2.x) {
        float d1 = length(gl_FragCoord.xy - v1);
        float d2 = length(gl_FragCoord.xy - v2);
        d = min(d1, d2);
    }
    return d;
}

void main()
{
    float d = verticalBarSDF(
        vec2(slider.start_x, slider.y),
        vec2(slider.end_x, slider.y)
    );

    float pd = verticalBarSDF(
        vec2(slider.start_x, slider.y),
        vec2(slider.knob_x, slider.y)
    );

    float m1 = 1.0 - smoothstep(5., 10., d);
    float mfill = 1.0 - smoothstep(2., 3., pd);
    float m2 = 1.0 - smoothstep(4., 5., d);
    m1 = clamp(m1 - m2, 0., 1.);
    m2 = clamp(m2 - mfill, 0., 1.);
    final_color = mix(vec4(0), vec4(0.9, 0.9, 0.9, 0.9), m1)
        + mix(vec4(0), vec4(0.1, 0.3, 0.15, 0.5), m2)
        + mix(vec4(0), vec4(0.2, 0.5, 0.3, 0.9), mfill);
}
