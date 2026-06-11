"""PYPOST-499: settings → open_settings → StorageManager encryption policy (PYPOST-481 debt)."""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import (
    ENCRYPTION_MODE_DEFAULT,
    ENCRYPTION_MODE_DISABLED,
    ENCRYPTION_MODE_ENABLED,
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


def _open_settings_with_mode(window, mode_data: str) -> AppSettings:
    original_init = SettingsDialog.__init__

    def init_and_configure(self, current, parent=None, *, storage=None):
        original_init(self, current, parent, storage=storage)
        index = self.env_encryption_mode_combo.findData(mode_data)
        assert index >= 0, f"unknown encryption mode {mode_data!r}"
        self.env_encryption_mode_combo.setCurrentIndex(index)

    def exec_accept(self):
        self.accept()
        return 1

    with (
        patch.object(SettingsDialog, "__init__", init_and_configure),
        patch.object(SettingsDialog, "exec", exec_accept),
        patch.object(window.style_manager, "apply_styles"),
        patch.object(window.env, "_on_env_changed"),
    ):
        window.open_settings()
    return window.settings


def _save_hidden_env(storage: StorageManager) -> dict:
    env = Environment(
        name=ENV_NAME,
        variables={SECRET_KEY: SECRET_VALUE, "VISIBLE": "public"},
        hidden_keys={SECRET_KEY},
    )
    storage.save_environments([env])
    with open(storage.environments_file, "r") as f:
        return json.load(f)[0]["variables"]


def _run_open_settings_chain(
    qapp,
    tmp_path,
    monkeypatch,
    caplog,
    *,
    mode_data: str,
    env_enabled: str | None,
    expect_encrypted: bool,
) -> None:
    storage = _make_storage(tmp_path, monkeypatch)
    if env_enabled is not None:
        monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", env_enabled)
    config_manager = MagicMock()
    window = _make_main_window(qapp, storage, config_manager)
    if expect_encrypted:
        fernet = pytest.importorskip("cryptography.fernet")
        monkeypatch.setenv(
            "PYPOST_ENV_ENCRYPTION_KEY",
            fernet.Fernet.generate_key().decode("utf-8"),
        )

    with caplog.at_level(logging.INFO):
        settings = _open_settings_with_mode(window, mode_data)

    config_manager.save_config.assert_called_once_with(settings)
    window.env.wait_storage_idle.assert_called_once()

    variables = _save_hidden_env(storage)
    secret_payload = variables[SECRET_KEY]
    if expect_encrypted:
        assert isinstance(secret_payload, dict)
        assert secret_payload.get("enc") is True
        assert variables["VISIBLE"] == "public"
    else:
        assert secret_payload == SECRET_VALUE

    assert any("storage_encryption_config_applied" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    ("mode_data", "env_enabled", "expect_encrypted"),
    [
        (ENCRYPTION_MODE_ENABLED, None, True),
        (ENCRYPTION_MODE_DISABLED, "true", False),
        (ENCRYPTION_MODE_DEFAULT, "true", True),
    ],
)
def test_open_settings_applies_encryption_policy_to_storage(
    qapp,
    tmp_path,
    monkeypatch,
    caplog,
    mode_data,
    env_enabled,
    expect_encrypted,
):
    _run_open_settings_chain(
        qapp,
        tmp_path,
        monkeypatch,
        caplog,
        mode_data=mode_data,
        env_enabled=env_enabled,
        expect_encrypted=expect_encrypted,
    )
