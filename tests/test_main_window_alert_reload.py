"""PYPOST-621: MainWindow reloads AlertManager after alert settings save."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.alert_manager import AlertManager
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import SettingsDialog
from tests.test_alert_manager import _make_payload

pytestmark = pytest.mark.timeout(60)

def _make_main_window(qapp, *, alert_manager=None):  # noqa: ARG001
    metrics = MagicMock()
    template_service = MagicMock()
    config_manager = MagicMock()
    mock_tabs = MagicMock()
    mock_collections = MagicMock()
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.mcp_server_controller.MCPServerManager"),
        patch("pypost.ui.main_window.CollectionsPresenter", return_value=mock_collections),
        patch("pypost.ui.main_window.TabsPresenter", return_value=mock_tabs),
        patch("pypost.ui.main_window.EnvPresenter"),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.wire_presenter_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
        patch("pypost.ui.main_window.resolve_encryption_enabled", return_value=False),
    ):
        mock_sm.return_value.settings = AppSettings()
        from pypost.ui.main_window import MainWindow

        window = MainWindow(
            metrics=metrics,
            template_service=template_service,
            config_manager=config_manager,
            alert_manager=alert_manager,
            history_manager=MagicMock(),
        )
    window.env = MagicMock()
    window.env.wait_storage_idle = MagicMock()
    window.collections = mock_collections
    window.tabs = mock_tabs
    window.settings_btn = MagicMock()
    return window

def _open_settings_with_webhook_url(window, webhook_url: str) -> AppSettings:
    original_init = SettingsDialog.__init__

    def init_and_configure(self, current, parent=None, *, storage=None):
        original_init(self, current, parent, storage=storage)
        self.alert_webhook_url_edit.setText(webhook_url)

    def exec_accept(self):
        self.accept()
        return 1

    with (
        patch.object(SettingsDialog, "__init__", init_and_configure),
        patch.object(SettingsDialog, "exec", exec_accept),
        patch.object(window.style_manager, "apply_styles"),
        patch.object(window.env, "reload_current_env"),
    ):
        window.open_settings()
    return window.settings

def _open_settings_with_alert_log_path(window, log_path: str) -> AppSettings:
    original_init = SettingsDialog.__init__

    def init_and_configure(self, current, parent=None, *, storage=None):
        original_init(self, current, parent, storage=storage)
        self.alert_log_path_edit.setText(log_path)

    def exec_accept(self):
        self.accept()
        return 1

    with (
        patch.object(SettingsDialog, "__init__", init_and_configure),
        patch.object(SettingsDialog, "exec", exec_accept),
        patch.object(window.style_manager, "apply_styles"),
        patch.object(window.env, "reload_current_env"),
    ):
        window.open_settings()
    return window.settings

def test_reload_alert_manager_closes_old_and_propagates_to_tabs(qapp, tmp_path):
    old_manager = MagicMock(spec=AlertManager)
    window = _make_main_window(qapp, alert_manager=old_manager)
    log_path = tmp_path / "alerts.log"
    window.settings = AppSettings(
        alert_webhook_url="https://hooks.example.com/new",
        alert_log_path=str(log_path),
    )

    with patch("pypost.ui.main_window.AlertManager") as mock_am_cls:
        new_manager = MagicMock(spec=AlertManager)
        mock_am_cls.return_value = new_manager
        window._reload_alert_manager()

    old_manager.close.assert_called_once()
    mock_am_cls.assert_called_once_with(
        log_path=log_path,
        webhook_url="https://hooks.example.com/new",
        webhook_auth_header=None,
    )
    window.tabs.set_alert_manager.assert_called_once_with(new_manager)

def test_open_settings_reloads_alert_manager_when_webhook_changes(qapp, caplog):
    initial = MagicMock(spec=AlertManager)
    window = _make_main_window(qapp, alert_manager=initial)
    window.settings = AppSettings()

    with (
        patch("pypost.ui.main_window.AlertManager") as mock_am_cls,
        caplog.at_level(logging.INFO),
    ):
        new_manager = MagicMock(spec=AlertManager)
        mock_am_cls.return_value = new_manager
        settings = _open_settings_with_webhook_url(
            window, "https://hooks.example.com/updated"
        )

    assert settings.alert_webhook_url == "https://hooks.example.com/updated"
    assert window._alert_manager is new_manager
    initial.close.assert_called_once()
    window.tabs.set_alert_manager.assert_called_with(new_manager)
    assert any("alert_manager_reloaded" in r.message for r in caplog.records)

def test_open_settings_skips_reload_when_alert_fields_unchanged(qapp):
    manager = MagicMock(spec=AlertManager)
    window = _make_main_window(qapp, alert_manager=manager)
    window.settings = AppSettings(font_size=14)

    original_init = SettingsDialog.__init__

    def init_and_configure(self, current, parent=None, *, storage=None):
        original_init(self, current, parent, storage=storage)
        self.font_size_spin.setValue(16)

    def exec_accept(self):
        self.accept()
        return 1

    with (
        patch.object(SettingsDialog, "__init__", init_and_configure),
        patch.object(SettingsDialog, "exec", exec_accept),
        patch.object(window.style_manager, "apply_styles"),
        patch.object(window.env, "reload_current_env"),
        patch.object(window, "_reload_alert_manager") as mock_reload,
    ):
        window.open_settings()

    mock_reload.assert_not_called()
    assert window._alert_manager is manager

def test_open_settings_emit_after_log_path_change_writes_to_new_file(qapp, tmp_path):
    old_log = tmp_path / "alerts-old.log"
    new_log = tmp_path / "alerts-new.log"
    initial = AlertManager(log_path=old_log)
    window = _make_main_window(qapp, alert_manager=initial)
    window.settings = AppSettings(alert_log_path=str(old_log))

    initial.emit(_make_payload(request_name="before-reload"))

    settings = _open_settings_with_alert_log_path(window, str(new_log))
    assert settings.alert_log_path == str(new_log)
    assert window._alert_manager is not initial

    window._alert_manager.emit(_make_payload(request_name="after-reload"))

    old_lines = [line for line in old_log.read_text().splitlines() if line.strip()]
    new_lines = [line for line in new_log.read_text().splitlines() if line.strip()]
    assert len(old_lines) == 1
    assert json.loads(old_lines[0])["request_name"] == "before-reload"
    assert len(new_lines) == 1
    assert json.loads(new_lines[0])["request_name"] == "after-reload"
