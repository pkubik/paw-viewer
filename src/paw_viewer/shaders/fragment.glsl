#version 420 core
in vec3 texture_coords;
in vec4 frag_crop_corners;
in vec2 frag_position;
out vec4 final_colors;

uniform sampler2D our_texture;

uniform float exposure;
uniform float gamma;

void main()
{
    // Flip Y here to avoid doing that when copying images to textures
    vec2 uv = vec2(texture_coords.x, 1. - texture_coords.y);
    final_colors = texture(our_texture, uv);
    
    vec4 exposure = vec4(vec3(exposure), 1.0);
    vec4 gamma = vec4(vec3(1.0 / gamma), 1.0);
    final_colors = pow(abs(final_colors * exposure), gamma);

    vec2 bottom_left = min(frag_crop_corners.xy, frag_crop_corners.zw);
    vec2 top_right = max(frag_crop_corners.xy, frag_crop_corners.zw);
    float eps = 0.000000001;
    if (length(bottom_left - top_right) > eps)
    {
        float dx1 = max(0., bottom_left.x - frag_position.x);
        float dy1 = max(0., bottom_left.y - frag_position.y);
        float dx2 = max(0., frag_position.x - top_right.x);
        float dy2 = max(0., frag_position.y - top_right.y);

        float min_d = max(dx1, dy1);
        min_d = max(min_d, dx2);
        min_d = max(min_d, dy2);
        if (min_d > 0)
        {
            final_colors = mix(final_colors, vec4(.1, .1, .1, 1.), 0.9);
        }
    }
}
