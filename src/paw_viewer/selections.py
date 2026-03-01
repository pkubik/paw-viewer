from dataclasses import dataclass
from pyglet.math import Vec2


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
        scale_x = to_size.x / from_size.x
        scale_y = to_size.y / from_size.y
        new = CropCorners(self.c1, self.c2)

        if round_pixels:
            new.c1 = Vec2(round(new.c1.x * scale_x), round(new.c1.y * scale_y))
            new.c2 = Vec2(round(new.c2.x * scale_x), round(new.c2.y * scale_y))
        else:
            new.c1 = Vec2(new.c1.x * scale_x, new.c1.y * scale_y)
            new.c2 = Vec2(new.c2.x * scale_x, new.c2.y * scale_y)

        return new


@dataclass
class TimeRange:
    start: int
    end: int

    def is_empty(self):
        return self.start >= self.end
