
import pytest

from unittest.mock import MagicMock, patch
from PySide6.QtGui import QShowEvent
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(60)


def _make_window(qapp):
    """Build a MainWindow with all heavy dependencies mocked."""
    metrics = MagicMock()
    template_service = MagicMock()
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.ConfigManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.mcp_server_controller.MCPServerManager"),
        patch("pypost.ui.main_window.CollectionsPresenter"),
        patch("pypost.ui.main_window.TabsPresenter"),
        patch("pypost.ui.main_window.EnvPresenter"),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.wire_presenter_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
    ):
        mock_sm.return_value.settings = AppSettings()
        from pypost.ui.main_window import MainWindow
        window = MainWindow(
            metrics=metrics,
            template_service=template_service,
            history_manager=MagicMock(),
        )
    return window

class TestApplySettingsFont:

    def test_apply_appearance_receives_font_size(self, qapp):
        window = _make_window(qapp)
        with patch.object(window.style_manager, "apply_appearance") as apply_appearance:
            window.apply_settings(AppSettings(font_size=18))
        apply_appearance.assert_called_once_with(
            qapp, theme="system", font_size=18
        )

    def test_apply_appearance_receives_theme(self, qapp):
        window = _make_window(qapp)
        with patch.object(window.style_manager, "apply_appearance") as apply_appearance:
            window.apply_settings(AppSettings(theme="dark"))
        apply_appearance.assert_called_once_with(
            qapp, theme="dark", font_size=12
        )

    def test_show_event_reapplies_settings_once(self, qapp):
        window = _make_window(qapp)
        with patch("pypost.ui.main_window.QTimer.singleShot") as single_shot:
            window.showEvent(QShowEvent())
            window.showEvent(QShowEvent())

        assert single_shot.call_count == 1
        delay_ms, scheduled = single_shot.call_args[0]
        assert delay_ms == 0
        assert callable(scheduled)
