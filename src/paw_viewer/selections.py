from dataclasses import dataclass
from pyglet.math import Vec2


def clip(x, min_x, max_x):
    return max(min(x, max_x), min_x)


def change_coords_resolution(
    coords: Vec2, from_size: Vec2, to_size: Vec2, round_pixels: bool = True
):
    scale_x = to_size.x / from_size.x
    scale_y = to_size.y / from_size.y

    new_x = coords.x * scale_x
    new_y = coords.y * scale_y
    if round_pixels:
        new_x = round(new_x)
        new_y = round(new_y)

    return Vec2(new_x, new_y)


@dataclass
class CropCorners:
    c1: Vec2 = Vec2()
    c2: Vec2 = Vec2()

    def crop_area(self):
        width = abs(self.c1.x - self.c2.x)
        height = abs(self.c1.y - self.c2.y)
        return width * height

    def change_resolution(
        self, from_size: Vec2, to_size: Vec2, round_pixels: bool = True
    ):
        """Assumes canonical coordinate system - origin at bottom-left, y increases upwards."""

        return CropCorners(
            change_coords_resolution(self.c1, from_size, to_size, round_pixels),
            change_coords_resolution(self.c2, from_size, to_size, round_pixels),
        )


@dataclass
class TimeRange:
    start: int
    end: int

    def is_empty(self):
        return self.start >= self.end
