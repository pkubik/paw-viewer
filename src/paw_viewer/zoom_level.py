class ZoomLevel:
    def __init__(self, min_log_scale: float = -8.0, max_log_scale: float = 8.0):
        self.log_scale = 0.0
        self.min_log_scale = min_log_scale
        self.max_log_scale = max_log_scale

    def scale(self) -> float:
        return 2**self.log_scale

    def zoom_in(self, increment: float = 0.25) -> float:
        current_scale = self.scale()
        self.log_scale = min(self.log_scale + increment, self.max_log_scale)
        new_scale = self.scale()
        return new_scale / current_scale

    def zoom_out(self, decrement: float = 0.25) -> float:
        return self.zoom_in(-decrement)

    def reset(self):
        self.log_scale = 0.0
