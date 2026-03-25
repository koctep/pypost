import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from pypost.models.settings import AppSettings


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_window(qapp):
    """Build a MainWindow with all heavy dependencies mocked."""
    metrics = MagicMock()
    template_service = MagicMock()
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.ConfigManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.main_window.MCPServerManager"),
        patch("pypost.ui.main_window.HistoryManager"),
        patch("pypost.ui.main_window.CollectionsPresenter"),
        patch("pypost.ui.main_window.TabsPresenter"),
        patch("pypost.ui.main_window.EnvPresenter"),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.MainWindow._wire_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
    ):
        mock_sm.return_value.settings = AppSettings()
        from pypost.ui.main_window import MainWindow
        window = MainWindow(metrics=metrics, template_service=template_service)
    # Supply widget stubs that apply_settings references via the explicit loop.
    window.settings_btn = MagicMock()
    return window


class TestApplySettingsFont:

    def test_font_size_applied_after_stylesheet(self, qapp):
        window = _make_window(qapp)
        settings = AppSettings(font_size=16)
        # apply_styles calls setStyleSheet("") which resets app font — this is the
        # real-world condition the fix must survive.
        with patch.object(
            window.style_manager, "apply_styles",
            side_effect=lambda app: app.setStyleSheet(""),
        ):
            window.apply_settings(settings)
        assert qapp.font().pointSize() == 16

    def test_font_size_min(self, qapp):
        window = _make_window(qapp)
        settings = AppSettings(font_size=8)
        with patch.object(
            window.style_manager, "apply_styles",
            side_effect=lambda app: app.setStyleSheet(""),
        ):
            window.apply_settings(settings)
        assert qapp.font().pointSize() == 8

    def test_font_size_second_call_wins(self, qapp):
        window = _make_window(qapp)
        with patch.object(
            window.style_manager, "apply_styles",
            side_effect=lambda app: app.setStyleSheet(""),
        ):
            window.apply_settings(AppSettings(font_size=14))
            window.apply_settings(AppSettings(font_size=20))
        assert qapp.font().pointSize() == 20
