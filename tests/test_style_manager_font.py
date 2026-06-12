"""PYPOST-106: StyleManager injects application font size into global QSS.
PYPOST-114: bundled main.qss includes QToolTip styling hook.
"""

import pytest

pytestmark = pytest.mark.timeout(60)

from PySide6.QtWidgets import QApplication, QWidget

from pypost.core.style_manager import StyleManager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_apply_styles_appends_font_size_rule(qapp):
    widget = QWidget()
    manager = StyleManager()
    manager.apply_styles(widget, font_size=16)
    assert "font-size: 16pt" in widget.styleSheet()


def test_apply_styles_without_font_size_omits_rule(qapp):
    widget = QWidget()
    manager = StyleManager()
    manager.apply_styles(widget)
    assert "Application font size" not in widget.styleSheet()


def test_load_styles_includes_tooltip_qss():
    manager = StyleManager()
    styles = manager.load_styles()
    assert "QToolTip" in styles
    assert "palette(tooltip-text)" in styles
    assert "palette(tooltip-base)" in styles
