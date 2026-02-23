"""Help overlay for paw-viewer displaying keyboard shortcuts and usage information."""

import pyglet
from pyglet.event import EventDispatcher

BASE_TEXT_COLOR = "#fefefe"
HEADER_TEXT_COLOR = "#118d26"
KEY_TEXT_COLOR = "#65b661"
FONT_SIZE = 4

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
        "Navigation",
        [
            ("Left-click + drag / WASD", "Pan the image"),
            ("SPACE", "Start/stop playback"),
            ("CTRL+A / CTRL+D", "Go to prev/next frame"),
            ("CTRL+S / CTRL+E", "Go to start/end frame"),
        ],
    )
    + format_section(
        "Zoom",
        [
            ("Mouse scroll / R/F", "Zoom in/out"),
            ("Double-Click", "Fit to window"),
        ],
    )
    + format_section(
        "Sources",
        [
            ("Z / X", "Prev/next source"),
            ("1-9", "Go to n-th source"),
            ("CTRL+Z / CTRL+X", "Prev/next source"),
        ],
    )
    + format_section(
        "Selection & Export",
        [
            ("Right-click + drag", "Select crop region"),
            ("Right-click", "Cancel crop region"),
            ("CTRL+X", "Copy region coordinates to clipboard"),
            ("CTRL+C", "Copy cropped image to clipboard"),
            ("CTRL+N", "Save cropped region as .npy"),
        ],
    )
    + format_section(
        "Other",
        [
            ("F1 / ?", "Show this help overlay"),
            ("CTRL+Q", "Quit"),
            ("ESC", "Close help overlay"),
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
        self.margin = 0.05
        self.background = None
        self.layout = None
        self._create_overlay()
        self.hide()

    def _create_overlay(self):
        """Create the help overlay label."""
        try:
            if self.background:
                self.background.delete()
            self.background = pyglet.shapes.Rectangle(
                x=self.margin * self.width,
                y=self.margin * self.height,
                width=int(self.width * (1 - self.margin * 2)),
                height=int(self.height * (1 - self.margin * 2)),
                color=(20, 26, 24, 220),
                batch=self.batch,
                group=self.group,
            )
            if self.layout:
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
        except Exception as e:
            print(f"Error creating help overlay: {e}")
            self.label = None

    def show(self):
        """Show the help overlay."""
        self.layout.visible = True
        self.background.visible = True

    def hide(self):
        """Hide the help overlay."""
        self.layout.visible = False
        self.background.visible = False

    def toggle(self):
        """Toggle overlay visibility."""
        self.layout.visible = not self.layout.visible
        self.background.visible = not self.background.visible

    def on_window_resize(self, width: int, height: int):
        """Handle window resize."""
        self.width = width
        self.height = height
        self._create_overlay()
