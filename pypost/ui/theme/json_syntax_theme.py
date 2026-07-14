from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QGuiApplication, QPalette


@dataclass(frozen=True)
class JsonSyntaxColors:
    """Foreground color names for JsonHighlighter token classes."""

    keyword: str = "darkblue"
    number: str = "blue"
    string: str = "green"
    key: str = "purple"
    placeholder: str = "darkorange"


DEFAULT_JSON_SYNTAX_COLORS = JsonSyntaxColors()

DARK_JSON_SYNTAX_COLORS = JsonSyntaxColors(
    keyword="#79c0ff",
    number="#56d4dd",
    string="#7ee787",
    key="#d2a8ff",
    placeholder="#ffa657",
)


def is_dark_palette(palette: QPalette | None = None) -> bool:
    """Return True when the application window palette reads as dark."""
    if palette is None:
        app = QGuiApplication.instance()
        if app is None:
            return False
        palette = app.palette()
    return palette.color(QPalette.ColorRole.Window).lightness() < 128


def resolve_json_syntax_colors(
    *,
    dark: bool | None = None,
    theme: str | None = None,
) -> JsonSyntaxColors:
    """Return JSON syntax colors for the active or requested theme."""
    if theme is not None:
        if theme == "dark":
            dark = True
        elif theme == "light":
            dark = False
        else:
            dark = is_dark_palette()
    elif dark is None:
        dark = is_dark_palette()
    return DARK_JSON_SYNTAX_COLORS if dark else DEFAULT_JSON_SYNTAX_COLORS
