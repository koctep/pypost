"""PYPOST-603: StyleManager theme application (Fusion palette vs system default)."""

import pytest

pytestmark = pytest.mark.timeout(60)

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from pypost.core.style_manager import StyleManager
from pypost.ui.styles.custom_style import PyPostStyle


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    
    # Save original style, palette, and stylesheet for isolation
    orig_style = app.style()
    orig_palette = app.palette()
    orig_stylesheet = app.styleSheet()
    
    # Reset/clear stylesheet to avoid style wrapping (QStyleSheetStyle)
    app.setStyleSheet("")
    
    yield app
    
    # Restore original state
    try:
        if orig_style:
            app.setStyle(orig_style)
    except RuntimeError:
        # If original style object was deleted/garbage-collected by Qt, fall back to PyPostStyle
        app.setStyle(PyPostStyle())
    app.setPalette(orig_palette)
    app.setStyleSheet(orig_stylesheet)


def test_apply_theme_dark_uses_fusion_and_dark_window(qapp):
    manager = StyleManager()
    manager.apply_theme(qapp, "dark")
    assert qapp.style().objectName().lower() == "fusion"
    assert qapp.palette().color(QPalette.ColorRole.Window).lightness() < 128


def test_apply_theme_light_uses_fusion_and_light_window(qapp):
    manager = StyleManager()
    manager.apply_theme(qapp, "light")
    assert qapp.style().objectName().lower() == "fusion"
    assert qapp.palette().color(QPalette.ColorRole.Window).lightness() >= 128


def test_apply_theme_system_restores_custom_style(qapp):
    manager = StyleManager()
    manager.apply_theme(qapp, "dark")
    manager.apply_theme(qapp, "system")
    assert isinstance(qapp.style(), PyPostStyle)


def test_apply_theme_unknown_value_falls_back_to_system(qapp):
    manager = StyleManager()
    manager.apply_theme(qapp, "dark")
    manager.apply_theme(qapp, "invalid")
    assert isinstance(qapp.style(), PyPostStyle)
