import pyglet


class ColumnLayout:
    """
    Column layout

    This is a super lazy column layout.
    Every element is assumed to have a fixed height that includes the spacing.
    Every element is anchored on the bottom-left.
    Each element is added right after the previous one, without any extra spacing.
    Elements need to handle any extra padding internally, if desired.
    Whenever a position of the column layout is changed, all elements are updated,
    by updating their x and y coordinates.

    The column itself can be anchored either top-left or bottom-left.
    This changes both the meaning of x, y coordinates and
    the way elements are ordered within the column.
    """

    def __init__(self, x: int, y: int, element_height, anchor: str = "top-left"):
        self.x = x
        self.y = y
        self.element_height = element_height  # Total height, including spacing
        self.anchor = anchor
        self.elements = []

    def add_widget(self, widget: pyglet.gui.widgets.WidgetBase) -> None:
        self.elements.append(widget)
        self.update_geometry()

    def update_geometry(self):
        if self.anchor == "top-left":
            initial_offset = -self.element_height
            offset = -self.element_height
        else:
            initial_offset = 0
            offset = self.element_height

        for i, element in enumerate(self.elements):
            element.update_geometry(x=self.x, y=initial_offset + self.y + i * offset)
