from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QStyleFactory

from pypost.ui.styles.custom_style import PyPostStyle

_THEME_SYSTEM = "system"
_THEME_LIGHT = "light"
_THEME_DARK = "dark"
_VALID_THEMES = {_THEME_SYSTEM, _THEME_LIGHT, _THEME_DARK}


def _fusion_dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    return palette


def _fusion_light_palette() -> QPalette:
    fusion = QStyleFactory.create("Fusion")
    return fusion.standardPalette()


class StyleManager:
    def __init__(self):
        # Path to pypost/ui/styles
        # This file is in pypost/core/style_manager.py, so parent.parent is pypost/
        self.root_dir = Path(__file__).parent.parent
        self.styles_dir = self.root_dir / "ui" / "styles"
        self.icons_dir = self.root_dir / "ui" / "resources" / "icons"

    def load_styles(self) -> str:
        """Reads all .qss files from the styles directory and returns the combined stylesheet."""
        if not self.styles_dir.exists():
            return ""

        combined_style = ""
        try:
            # Sort files to ensure deterministic loading order (e.g. alphabetical)
            qss_files = sorted(self.styles_dir.glob("*.qss"))

            for file_path in qss_files:
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        combined_style += f"\n/* File: {file_path.name} */\n{content}\n"
                except Exception as e:
                    print(f"Error reading style file {file_path}: {e}")

        except Exception as e:
            print(f"Error scanning styles directory: {e}")

        # Replace placeholders with absolute path
        # Convert to absolute path and resolve any symlinks
        icons_path = self.icons_dir.resolve().as_posix()
        combined_style = combined_style.replace("%ICONS_DIR%", icons_path)

        return combined_style

    def _font_size_rule(self, font_size: int) -> str:
        return f"\n/* Application font size */\nQWidget {{ font-size: {font_size}pt; }}\n"

    def apply_theme(self, app, theme: str = _THEME_SYSTEM) -> None:
        """Apply Qt Fusion palette for light/dark, or system default style."""
        if theme not in _VALID_THEMES:
            theme = _THEME_SYSTEM

        if theme == _THEME_SYSTEM:
            custom_style = PyPostStyle()
            custom_style.set_close_button_size(48)
            app.setStyle(custom_style)
            app.setPalette(custom_style.standardPalette())
            return

        fusion = QStyleFactory.create("Fusion")
        app.setStyle(fusion)
        if theme == _THEME_DARK:
            app.setPalette(_fusion_dark_palette())
        else:
            app.setPalette(_fusion_light_palette())

    def apply_styles(self, app_or_widget, font_size: int | None = None):
        """Applies the loaded styles to the given application or widget."""
        style_sheet = self.load_styles()
        if font_size is not None:
            style_sheet += self._font_size_rule(font_size)
        # Replace existing stylesheet to avoid accumulation on reload
        app_or_widget.setStyleSheet(style_sheet)
