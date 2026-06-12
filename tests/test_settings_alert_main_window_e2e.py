"""PYPOST-620: MainWindow settings save persists alert fields to settings.json."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from pypost.core.config_manager import ConfigManager
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import SettingsDialog

pytestmark = pytest.mark.timeout(120)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_main_window(qapp, config_manager):  # noqa: ARG001
    metrics = MagicMock()
    template_service = MagicMock()
    mock_tabs = MagicMock()
    mock_collections = MagicMock()
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.main_window.MCPServerManager"),
        patch("pypost.ui.main_window.HistoryManager"),
        patch(
            "pypost.ui.main_window.CollectionsPresenter",
            return_value=mock_collections,
        ),
        patch("pypost.ui.main_window.TabsPresenter", return_value=mock_tabs),
        patch("pypost.ui.main_window.EnvPresenter"),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.wire_presenter_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
        patch("pypost.ui.main_window.resolve_encryption_enabled", return_value=False),
        patch("pypost.ui.main_window.AlertManager"),
    ):
        mock_sm.return_value.settings = config_manager.load_config()
        from pypost.ui.main_window import MainWindow

        window = MainWindow(
            metrics=metrics,
            template_service=template_service,
            config_manager=config_manager,
        )
    window.storage = MagicMock()
    window.env = MagicMock()
    window.env.wait_storage_idle = MagicMock()
    window.collections = mock_collections
    window.tabs = mock_tabs
    window.settings_btn = MagicMock()
    return window


def _open_settings_with_alert_fields(
    window,
    *,
    log_path: str,
    webhook_url: str,
    webhook_auth: str,
) -> AppSettings:
    original_init = SettingsDialog.__init__

    def init_and_configure(self, current, parent=None, *, storage=None):
        original_init(self, current, parent, storage=storage)
        self.alert_log_path_edit.setText(log_path)
        self.alert_webhook_url_edit.setText(webhook_url)
        self.alert_webhook_auth_edit.setText(webhook_auth)

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


def test_open_settings_alert_fields_round_trip_via_settings_json(qapp, tmp_path):
    """Settings save through MainWindow persists alert fields to disk."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    with patch("pypost.core.config_manager.user_config_dir", return_value=str(config_dir)):
        config_manager = ConfigManager()
        window = _make_main_window(qapp, config_manager)
        window.settings = config_manager.load_config()

        log_path = str(tmp_path / "custom-alerts.log")
        webhook_url = "https://hooks.example.com/pypost"
        webhook_auth = "Bearer round-trip-token"

        settings = _open_settings_with_alert_fields(
            window,
            log_path=log_path,
            webhook_url=webhook_url,
            webhook_auth=webhook_auth,
        )

        assert settings.alert_log_path == log_path
        assert settings.alert_webhook_url == webhook_url
        assert settings.alert_webhook_auth_header == webhook_auth

        cfg_path = Path(config_dir) / "settings.json"
        on_disk = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert on_disk["alert_log_path"] == log_path
        assert on_disk["alert_webhook_url"] == webhook_url
        assert on_disk["alert_webhook_auth_header"] == webhook_auth

        reloaded = ConfigManager().load_config()
        assert reloaded.alert_log_path == log_path
        assert reloaded.alert_webhook_url == webhook_url
        assert reloaded.alert_webhook_auth_header == webhook_auth
