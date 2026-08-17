"""PYPOST-508: graceful shutdown waits for environment storage gateway."""

import pytest

pytestmark = pytest.mark.timeout(120)

from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from pypost.models.settings import AppSettings

def _make_window(qapp):
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
    window.settings_btn = MagicMock()
    window.env = MagicMock()
    window.env.wait_storage_idle = MagicMock(return_value=True)
    return window

def test_handle_exit_waits_for_storage_when_encryption_enabled(qapp, monkeypatch):
    window = _make_window(qapp)
    window.settings = AppSettings(env_encryption_enabled=True)
    with patch("pypost.ui.main_window.QApplication") as mock_qapp:
        mock_qapp.instance.return_value = MagicMock()
        window.handle_exit()
    window.env.wait_storage_idle.assert_called_once()

def test_handle_exit_skips_storage_wait_when_encryption_disabled(qapp):
    window = _make_window(qapp)
    window.settings = AppSettings(env_encryption_enabled=False)
    with patch("pypost.ui.main_window.QApplication") as mock_qapp:
        mock_qapp.instance.return_value = MagicMock()
        window.handle_exit()
    window.env.wait_storage_idle.assert_not_called()

def test_handle_exit_flushes_pending_state_manager_save(qapp):
    window = _make_window(qapp)
    window.settings = AppSettings(env_encryption_enabled=False)
    with patch("pypost.ui.main_window.QApplication") as mock_qapp:
        mock_qapp.instance.return_value = MagicMock()
        window.handle_exit()
    window.state_manager.flush_pending_save.assert_called_once()
