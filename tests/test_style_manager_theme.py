"""PYPOST-603: StyleManager theme application (Fusion palette vs system default)."""

import pytest

from PySide6.QtGui import QPalette

from pypost.ui.styles.style_manager import StyleManager
from pypost.ui.styles.custom_style import PyPostStyle

pytestmark = pytest.mark.timeout(60)


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
