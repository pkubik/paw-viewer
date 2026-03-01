"""Help overlay for paw-viewer displaying keyboard shortcuts and usage information."""

import pyglet
from pyglet.event import EventDispatcher

from paw_viewer.style import FG_COLOR

BASE_TEXT_COLOR = "#fefefe"
HEADER_TEXT_COLOR = "#118d26"
KEY_TEXT_COLOR = "#65b661"
FONT_SIZE = 5

HELP_KEY_ENTRY_HTML_TEMPLATE = (
    f'<font size="{FONT_SIZE}" color="{KEY_TEXT_COLOR}" face="monospace">'
    f"<b>{{key}}: </b></font> "
    f'<font color="{BASE_TEXT_COLOR}" size="{FONT_SIZE}" face="monospace">{{description}}</font>'
    "<br>"
)


def format_section(title: str, entries: list[tuple[str, str]]) -> str:
    """Format a section of the help overlay."""
    section_html = (
        f"<h2><font color='{HEADER_TEXT_COLOR}' face='monospace'>{title}</font></h2>"
    )
    for key, description in entries:
        section_html += HELP_KEY_ENTRY_HTML_TEMPLATE.format(
            key=key, description=description
        )
    return section_html


HELP_HTML = (
    f"<h1><font color='{HEADER_TEXT_COLOR}' face='monospace'>KEYBOARD SHORTCUTS</font></h1><BR>"
    + format_section(
        "Help",
        [
            ("F1 / ?", "Show this help overlay"),
            ("Mouse scroll", "Scroll help overlay while visible"),
            ("ESC", "Close help overlay"),
        ],
    )
    + format_section(
        "Navigation",
        [
            ("Left-click+drag / WASD", "Pan the image"),
            ("SPACE", "Start/stop playback"),
            ("CTRL+A / CTRL+D", "Go to prev/next frame"),
            ("CTRL+S / CTRL+E", "Go to start/end frame"),
            ("Left-click+drag on slider", "Select frame"),
            ("B", "Toggle forward/backward playback"),
            ("Shift+B", "Toggle back-and-forth playback"),
        ],
    )
    + format_section(
        "Zoom",
        [
            ("Mouse scroll / R/F", "Zoom in/out"),
        ],
    )
    + format_section(
        "Sources",
        [
            ("Z / X", "Prev/next source"),
            ("1-9", "Go to n-th source"),
        ],
    )
    + format_section(
        "Selection & Export",
        [
            ("Right-click+drag", "Select crop region"),
            ("Right-click", "Cancel crop region"),
            ("Right-click+drag on slider", "Select time range"),
            ("CTRL+X", "Copy region coordinates to clipboard"),
            ("CTRL+C", "Copy cropped image to clipboard"),
            ("CTRL+N", "Save cropped region as .npy"),
        ],
    )
    + format_section(
        "Other",
        [
            ("CTRL+Q", "Quit"),
        ],
    )
)


class HelpOverlay(EventDispatcher):
    """Displays a help overlay in the viewer window."""

    def __init__(
        self,
        width: int,
        height: int,
        batch: pyglet.graphics.Batch,
        group: pyglet.graphics.Group,
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.batch = batch
        self.group = group
        self.visible = False
        self.margin = 0.04
        self.background = None
        self.layout = None
        self.label = None
        self.visible = False
        self._create_overlay()

    def _create_overlay(self):
        """Create the help overlay label."""
        if self.label:
            self.label.delete()
        self.label = pyglet.text.Label(
            "F1 / ? for help",
            font_name="Lucida Console",
            font_size=14,
            color=FG_COLOR,
            x=self.width - 8,
            y=self.height - 8,
            anchor_x="right",
            anchor_y="top",
            batch=self.batch,
            group=self.group,
        )

        if self.background:
            self.background.delete()
        self.background = pyglet.shapes.BorderedRectangle(
            x=self.margin * self.width,
            y=self.margin * self.height,
            width=int(self.width * (1 - self.margin * 2)),
            height=int(self.height * (1 - self.margin * 2)),
            border=5,
            color=(20, 26, 24, 240),
            border_color=(100, 200, 100, 240),
            batch=self.batch,
            group=self.group,
        )

        scroll_offset = 0
        if self.layout:
            scroll_offset = self.layout.view_y  # to preserve scroll on window resize
            self.layout.delete()
        self.layout = pyglet.text.layout.ScrollableTextLayout(
            pyglet.text.decode_html(HELP_HTML),
            x=2 * self.margin * self.width,
            y=2 * self.margin * self.height,
            batch=self.batch,
            group=self.group,
            multiline=True,
            width=int(self.width * (1 - self.margin * 4)),
            height=int(self.height * (1 - self.margin * 4)),
        )
        self.layout.view_y = scroll_offset

        if self.visible:
            self.show()
        else:
            self.hide()

    def show(self):
        """Show the help overlay."""
        self.visible = True
        self.label.visible = False
        self.layout.visible = True
        self.background.visible = True

    def hide(self):
        """Hide the help overlay."""
        self.visible = False
        self.label.visible = True
        self.layout.visible = False
        self.background.visible = False

    def toggle(self):
        """Toggle overlay visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()

    def on_window_resize(self, width: int, height: int):
        """Handle window resize."""
        self.width = width
        self.height = height
        self._create_overlay()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.layout and self.layout.visible:
            self.layout.view_y += 20 * scroll_y
            return pyglet.event.EVENT_HANDLED

    def on_key_press(self, symbol, modifiers):
        if self.layout is None:
            return pyglet.event.EVENT_UNHANDLED

        if self.layout.visible:
            if symbol in (
                pyglet.window.key.ESCAPE,
                pyglet.window.key.F1,
                pyglet.window.key.SLASH,
            ):
                self.hide()
                return pyglet.event.EVENT_HANDLED
        else:
            if symbol in (pyglet.window.key.F1, pyglet.window.key.SLASH):
                self.show()
                return pyglet.event.EVENT_HANDLED
        return pyglet.event.EVENT_UNHANDLED
