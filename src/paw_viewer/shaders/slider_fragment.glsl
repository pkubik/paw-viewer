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
    int steps;
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

    // TODO: avoid hardcoded widths and colors
    float full_mask = 1.0 - smoothstep(4., 8., d);
    float inner_filled_mask = 1.0 - smoothstep(1.5, 2., pd);
    float inner_mask = 1.0 - smoothstep(3., 4., d);

    // Compose slider colors
    float outline_mask = clamp(full_mask - inner_mask, 0., 1.);
    float inner_unfilled_mask = clamp(inner_mask - inner_filled_mask, 0., 1.);
    final_color = mix(vec4(0), vec4(0.9, 0.9, 0.9, 0.6), outline_mask)
        + mix(vec4(0), vec4(0.1, 0.2, 0.15, 0.8), inner_unfilled_mask)
        + mix(vec4(0), vec4(0.2, 0.5, 0.3, 0.9), inner_filled_mask);

    // Add splitters
    float inner_length = slider.end_x - slider.start_x;

    float steps = float(slider.steps);
    float step_width = inner_length / float(slider.steps);
    while (step_width < 8.)
    {
        steps /= 10;
        step_width *= 10;
    }

    float rel_x = (gl_FragCoord.x - slider.start_x) / inner_length;
    float rel_segment_x = fract(rel_x * float(steps));
    float rel_splitter_distance = min(rel_segment_x, 1 - rel_segment_x);
    float splitter_distance = rel_splitter_distance * step_width;
    float splitter_mask = float(splitter_distance < 1.0);
    final_color = mix(final_color, vec4(0.2, 0.6, 0.3, 1), min(inner_mask, splitter_mask));
}
