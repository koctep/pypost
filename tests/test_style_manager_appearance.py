"""PYPOST-793: StyleManager.apply_appearance full appearance pipeline."""

import pytest

from unittest.mock import MagicMock, patch

from pypost.ui.styles.style_manager import StyleManager

pytestmark = pytest.mark.timeout(60)


def test_apply_appearance_calls_apply_theme(qapp):
    manager = StyleManager()
    with patch.object(manager, "apply_theme") as apply_theme:
        manager.apply_appearance(qapp, theme="dark", font_size=12)
    apply_theme.assert_called_once_with(qapp, "dark")

def test_apply_appearance_stylesheet_contains_font_rule(qapp):
    manager = StyleManager()
    manager.apply_appearance(qapp, theme="light", font_size=16)
    assert "font-size: 16pt" in qapp.styleSheet()

def test_apply_appearance_sets_application_font(qapp):
    manager = StyleManager()
    manager.apply_appearance(qapp, theme="system", font_size=18)
    assert qapp.font().pointSize() == 18

def test_font_size_survives_stylesheet_reset(qapp):
    manager = StyleManager()
    with patch.object(
        manager,
        "apply_styles",
        side_effect=lambda app, font_size=None: app.setStyleSheet(""),
    ):
        manager.apply_appearance(qapp, theme="system", font_size=16)
    assert qapp.font().pointSize() == 16

def test_font_size_min(qapp):
    manager = StyleManager()
    with patch.object(
        manager,
        "apply_styles",
        side_effect=lambda app, font_size=None: app.setStyleSheet(""),
    ):
        manager.apply_appearance(qapp, theme="system", font_size=8)
    assert qapp.font().pointSize() == 8

def test_font_size_second_call_wins(qapp):
    manager = StyleManager()
    with patch.object(
        manager,
        "apply_styles",
        side_effect=lambda app, font_size=None: app.setStyleSheet(""),
    ):
        manager.apply_appearance(qapp, theme="system", font_size=14)
        manager.apply_appearance(qapp, theme="system", font_size=20)
    assert qapp.font().pointSize() == 20

def test_apply_appearance_call_order(qapp):
    manager = StyleManager()
    call_order: list[str] = []

    def track_theme(app, theme):
        call_order.append("theme")
        return MagicMock()

    def track_styles(app, font_size=None):
        call_order.append("styles")

    with (
        patch.object(manager, "apply_theme", side_effect=track_theme),
        patch.object(manager, "apply_styles", side_effect=track_styles),
        patch.object(qapp, "setFont", side_effect=lambda f: call_order.append("font")),
    ):
        manager.apply_appearance(qapp, theme="dark", font_size=12)

    assert call_order == ["theme", "styles", "font"]
