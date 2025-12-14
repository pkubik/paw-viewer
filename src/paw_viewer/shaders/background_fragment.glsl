#version 420 core
out vec4 final_colors;

// Grid parameters
const float GRID_THICKNESS = 2.0;
const float MAJOR_SCALE = 32.0; // Size of the major grid cells (e.g., 10 meters)

// Function to calculate grid line visibility
float grid_intensity(float coordinate, float scale, float thickness)
{
    float line_pos = mod(coordinate, scale);
    float near_line = min(line_pos, scale - line_pos) / thickness;
    return 1. - near_line;
}

void main()
{
    float x_grid = grid_intensity(gl_FragCoord.x, MAJOR_SCALE, GRID_THICKNESS);
    float y_grid = grid_intensity(gl_FragCoord.y, MAJOR_SCALE, GRID_THICKNESS);
    float grid = max(x_grid, y_grid);
    final_colors = vec4(.3, .6, .4, grid * 0.5);
}
