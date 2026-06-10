"""Settings UI and persistence for environment encryption (PYPOST-481)."""

import pytest
from PySide6.QtWidgets import QApplication

from pypost.core.config_manager import ConfigManager
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import (
    ENCRYPTION_MODE_DISABLED,
    ENCRYPTION_MODE_ENABLED,
    KEY_SOURCE_ENVIRONMENT,
    KEY_SOURCE_KEYRING,
    KEY_SOURCE_SECRET_STORE,
    SettingsDialog,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestSettingsDialogEnvironmentEncryption:
    def test_encryption_controls_on_form(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert dlg.env_encryption_mode_combo.parent() is dlg
            assert dlg.form_layout.indexOf(dlg.env_encryption_mode_combo) >= 0
            assert dlg.form_layout.indexOf(dlg.env_encryption_key_source_combo) >= 0
            assert (
                dlg.form_layout.indexOf(
                    dlg.env_encryption_key_source_fallback_edit,
                )
                >= 0
            )
        finally:
            dlg.close()

    def test_key_source_combo_includes_all_sources(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            combo = dlg.env_encryption_key_source_combo
            sources = [combo.itemData(i) for i in range(combo.count())]
            assert sources == [
                KEY_SOURCE_ENVIRONMENT,
                KEY_SOURCE_KEYRING,
                KEY_SOURCE_SECRET_STORE,
            ]
        finally:
            dlg.close()

    def test_fallback_loads_from_settings(self, qapp):
        dlg = SettingsDialog(
            AppSettings(
                env_encryption_key_source_fallback=["environment", "secret_store"],
            ),
        )
        try:
            assert dlg.env_encryption_key_source_fallback_edit.text() == "environment,secret_store"
        finally:
            dlg.close()

    def test_help_text_updates_for_key_source(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            keyring_index = dlg.env_encryption_key_source_combo.findData(
                KEY_SOURCE_KEYRING,
            )
            dlg.env_encryption_key_source_combo.setCurrentIndex(keyring_index)
            assert "keyring" in dlg.env_encryption_help_label.text().lower()
        finally:
            dlg.close()

    def test_encryption_mode_loads_from_settings(self, qapp):
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True))
        try:
            assert dlg.env_encryption_mode_combo.currentData() == ENCRYPTION_MODE_ENABLED
        finally:
            dlg.close()

    def test_accept_persists_encryption_fields(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            dlg.env_encryption_mode_combo.setCurrentIndex(1)
            dlg.accept()
            settings = dlg.get_settings()
            assert settings.env_encryption_enabled is True
            assert settings.env_encryption_key_source == KEY_SOURCE_ENVIRONMENT
        finally:
            dlg.close()

    def test_accept_persists_fallback_chain(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            keyring_index = dlg.env_encryption_key_source_combo.findData(
                KEY_SOURCE_KEYRING,
            )
            dlg.env_encryption_key_source_combo.setCurrentIndex(keyring_index)
            dlg.env_encryption_key_source_fallback_edit.setText(
                "environment, secret_store",
            )
            dlg.accept()
            settings = dlg.get_settings()
            assert settings.env_encryption_key_source == KEY_SOURCE_KEYRING
            assert settings.env_encryption_key_source_fallback == [
                "environment",
                "secret_store",
            ]
        finally:
            dlg.close()

    def test_accept_default_mode_stores_none(self, qapp):
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True))
        try:
            dlg.env_encryption_mode_combo.setCurrentIndex(0)
            dlg.accept()
            assert dlg.get_settings().env_encryption_enabled is None
        finally:
            dlg.close()

    def test_accept_disabled_mode(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            disabled_index = dlg.env_encryption_mode_combo.findData(
                ENCRYPTION_MODE_DISABLED,
            )
            dlg.env_encryption_mode_combo.setCurrentIndex(disabled_index)
            dlg.accept()
            assert dlg.get_settings().env_encryption_enabled is False
        finally:
            dlg.close()


class TestConfigManagerEncryptionPersistence:
    def test_save_load_encryption_fields(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pypost.core.config_manager.user_config_dir",
            lambda app_name, app_author: str(tmp_path),
        )
        cm = ConfigManager()
        settings = cm.load_config()
        settings.env_encryption_enabled = True
        settings.env_encryption_key_source = KEY_SOURCE_ENVIRONMENT
        settings.env_encryption_key_source_fallback = ["secret_store"]
        cm.save_config(settings)

        reloaded = ConfigManager().load_config()
        assert reloaded.env_encryption_enabled is True
        assert reloaded.env_encryption_key_source == KEY_SOURCE_ENVIRONMENT
        assert reloaded.env_encryption_key_source_fallback == ["secret_store"]
