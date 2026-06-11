"""PYPOST-501: settings key source → open_settings → StorageManager encrypt/decrypt."""


import pytest

pytestmark = pytest.mark.timeout(120)

import json
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from pypost.core.key_provider import build_key_id
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import (
    ENCRYPTION_MODE_ENABLED,
    KEY_SOURCE_ENVIRONMENT,
    KEY_SOURCE_SECRET_STORE,
    SettingsDialog,
)

ENV_NAME = "Dev"
SECRET_KEY = "SECRET"
SECRET_VALUE = "s3cr3t"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    return StorageManager()


def _make_main_window(qapp, storage, config_manager):  # noqa: ARG001
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
        patch("pypost.ui.main_window.CollectionsPresenter", return_value=mock_collections),
        patch("pypost.ui.main_window.TabsPresenter", return_value=mock_tabs),
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

        window = MainWindow(
            metrics=metrics,
            template_service=template_service,
            config_manager=config_manager,
        )
    window.storage = storage
    window.env = MagicMock()
    window.env.wait_storage_idle = MagicMock()
    window.collections = mock_collections
    window.tabs = mock_tabs
    window.settings_btn = MagicMock()
    mock_tabs.widget.tabBar.return_value = MagicMock()
    return window


def _open_settings_with_key_source(
    window,
    *,
    key_source: str,
    fallback_text: str,
) -> AppSettings:
    original_init = SettingsDialog.__init__

    def init_and_configure(self, current, parent=None, *, storage=None):
        original_init(self, current, parent, storage=storage)
        enabled_index = self.env_encryption_mode_combo.findData(ENCRYPTION_MODE_ENABLED)
        self.env_encryption_mode_combo.setCurrentIndex(enabled_index)
        source_index = self.env_encryption_key_source_combo.findData(key_source)
        assert source_index >= 0
        self.env_encryption_key_source_combo.setCurrentIndex(source_index)
        self.env_encryption_key_source_fallback_edit.setText(fallback_text)

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


def test_open_settings_secret_store_with_env_fallback_encrypt_decrypt_round_trip(
    qapp,
    tmp_path,
    monkeypatch,
):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    fallback_key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", fallback_key)

    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps({"active_key_id": key_id, "keys": {key_id: key}}),
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "active_key_id": key_id,
                "keys": {key_id: key},
                "backends": [{"type": "file", "path": str(registry_path)}],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", str(spec_path))

    storage = _make_storage(tmp_path, monkeypatch)
    config_manager = MagicMock()
    window = _make_main_window(qapp, storage, config_manager)

    settings = _open_settings_with_key_source(
        window,
        key_source=KEY_SOURCE_SECRET_STORE,
        fallback_text=KEY_SOURCE_ENVIRONMENT,
    )
    assert settings.env_encryption_key_source == KEY_SOURCE_SECRET_STORE
    assert settings.env_encryption_key_source_fallback == [KEY_SOURCE_ENVIRONMENT]
    assert settings.env_encryption_enabled is True

    env = Environment(
        name=ENV_NAME,
        variables={SECRET_KEY: SECRET_VALUE},
        hidden_keys={SECRET_KEY},
    )
    storage.save_environments([env])
    reloaded = storage.load_environments()
    assert len(reloaded) == 1
    assert reloaded[0].variables[SECRET_KEY] == SECRET_VALUE
