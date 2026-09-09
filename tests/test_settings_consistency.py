"""Regression coverage for the authoritative settings snapshot and atomic store."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog

from pypost.core.config_manager import (
    ConfigManager,
    ConfigPersistenceError,
    ConfigRecoveryNotice,
)
from pypost.core.qt.state_manager import StateManager
from pypost.models.settings import AppSettings
from pypost.ui import main_window_settings

pytestmark = pytest.mark.timeout(60)


class _AcceptedSettingsDialog:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def exec(self) -> int:
        return QDialog.DialogCode.Accepted

    def get_settings(self) -> AppSettings:
        return self._settings

    def cleanup(self) -> None:
        pass

    def deleteLater(self) -> None:
        pass


def _settings_window(settings, state_manager, config_manager, candidate):
    dialog = _AcceptedSettingsDialog(candidate)
    return SimpleNamespace(
        _teardown_started=False,
        settings=settings,
        state_manager=state_manager,
        config_manager=config_manager,
        storage=MagicMock(),
        env=MagicMock(),
        metrics=MagicMock(),
        apply_settings=MagicMock(),
        _alert_settings_changed=MagicMock(return_value=False),
        _reload_alert_manager=MagicMock(),
    ), lambda *_args, **_kwargs: dialog


def test_preferences_survive_ui_state_debounce_and_snapshot_identity(qapp, tmp_path):
    """A pending debounce may not overwrite preferences saved by Settings."""
    config_manager = ConfigManager(config_dir=tmp_path)
    settings = AppSettings(
        theme="system",
        font_size=12,
        open_tabs=["initial"],
        expanded_collections=["collection-1"],
        last_environment_id="environment-1",
    )
    state_manager = StateManager(config_manager, settings)
    state_manager.set_open_tabs(["scheduled-before-dialog"])

    candidate = settings.model_copy(update={"theme": "dark", "font_size": 18})
    window, dialog_factory = _settings_window(
        settings, state_manager, config_manager, candidate
    )
    main_window_settings.open_settings(window, dialog_factory)

    assert window.settings is settings
    assert state_manager.settings is settings
    assert settings.theme == "dark"
    assert settings.font_size == 18

    state_manager.set_open_tabs(["request-2"])
    state_manager.set_expanded_collections(["collection-2"])
    state_manager.set_last_environment_id("environment-2")
    QTest.qWait(350)

    reloaded = ConfigManager(config_dir=tmp_path).load_config()
    assert reloaded.theme == "dark"
    assert reloaded.font_size == 18
    assert reloaded.open_tabs == ["request-2"]
    assert reloaded.expanded_collections == ["collection-2"]
    assert reloaded.last_environment_id == "environment-2"


def test_compose_app_loads_once_and_shares_settings_identity(qapp, tmp_path):
    authoritative = AppSettings()
    config_manager = MagicMock()
    config_manager.load_config.return_value = authoritative
    state_manager = MagicMock()
    state_manager.settings = authoritative
    registry = MagicMock()

    def make_window(**kwargs):
        return SimpleNamespace(
            settings=kwargs["settings"],
            state_manager=kwargs["state_manager"],
            mcp_controller=SimpleNamespace(registry=registry),
            start_initial_loads=MagicMock(),
        )

    with (
        patch("pypost.main.ConfigManager", return_value=config_manager),
        patch("pypost.main.StateManager", return_value=state_manager) as state_cls,
        patch("pypost.main.MetricsManager"),
        patch("pypost.main.TemplateService"),
        patch("pypost.main.AlertManager"),
        patch("pypost.main.HistoryManager"),
        patch("pypost.main.StorageManager"),
        patch("pypost.main.RequestManager"),
        patch("pypost.main.MCPServerManager"),
        patch("pypost.main.MainWindow", side_effect=make_window) as window_cls,
    ):
        from pypost.main import compose_app

        composed = compose_app(config_dir=tmp_path, apply_log_level=False)

    config_manager.load_config.assert_called_once_with()
    state_cls.assert_called_once_with(config_manager, authoritative)
    window_kwargs = window_cls.call_args.kwargs
    assert window_kwargs["settings"] is authoritative
    assert window_kwargs["state_manager"] is state_manager
    assert window_kwargs["defer_startup"] is True
    assert composed.settings is composed.window.settings
    assert composed.settings is composed.window.state_manager.settings


@pytest.mark.parametrize("failure_target", ["json.dump", "os.replace"])
def test_failed_atomic_save_keeps_revision_and_primary_file(tmp_path, failure_target):
    config_manager = ConfigManager(config_dir=tmp_path)
    settings = AppSettings(theme="light")
    config_manager.save_config(settings)
    original_revision = settings.revision
    original_contents = config_manager.config_path.read_bytes()
    settings.theme = "dark"

    with patch(
        f"pypost.core.config_manager.{failure_target}",
        side_effect=OSError("disk failure"),
    ):
        with pytest.raises(ConfigPersistenceError):
            config_manager.save_config(settings)

    assert settings.revision == original_revision
    assert config_manager.config_path.read_bytes() == original_contents
    assert not list(tmp_path.glob(".settings.json.*.tmp"))


def test_corrupt_settings_are_quarantined_with_recovery_notice(tmp_path):
    config_path = tmp_path / "settings.json"
    config_path.write_text("{broken", encoding="utf-8")
    config_manager = ConfigManager(config_dir=tmp_path)

    assert config_manager.load_config() == AppSettings()
    notice = config_manager.recovery_notice
    assert notice is not None
    assert notice.category == "malformed_json"
    assert notice.quarantine_path is not None
    assert notice.quarantine_path.read_text(encoding="utf-8") == "{broken"
    assert not config_path.exists()


def test_settings_dialog_save_failure_is_visible_and_does_not_apply(qapp, tmp_path):
    config_manager = ConfigManager(config_dir=tmp_path)
    settings = AppSettings(theme="light")
    state_manager = StateManager(config_manager, settings)
    candidate = settings.model_copy(update={"theme": "dark"})
    window, dialog_factory = _settings_window(
        settings, state_manager, config_manager, candidate
    )

    with (
        patch.object(
            config_manager,
            "save_config",
            side_effect=ConfigPersistenceError(config_manager.config_path, "replace"),
        ),
        patch.object(main_window_settings, "show_settings_save_failed") as show_error,
    ):
        main_window_settings.open_settings(window, dialog_factory)

    assert settings.theme == "light"
    assert settings.revision == 0
    window.apply_settings.assert_not_called()
    show_error.assert_called_once()


def test_debounced_save_failure_emits_error_and_remains_pending(qapp, tmp_path):
    config_manager = ConfigManager(config_dir=tmp_path)
    settings = AppSettings()
    state_manager = StateManager(config_manager, settings)
    errors: list[str] = []
    state_manager.persistence_failed.connect(errors.append)
    state_manager.set_open_tabs(["request"])

    with patch.object(
        config_manager,
        "save_config",
        side_effect=ConfigPersistenceError(config_manager.config_path, "replace"),
    ):
        QTest.qWait(350)

    assert errors
    assert state_manager._save_pending is True
    assert settings.revision == 0


def test_atomic_save_writes_complete_json_and_advances_revision(tmp_path):
    config_manager = ConfigManager(config_dir=tmp_path)
    settings = AppSettings(theme="dark", open_tabs=["one"])

    config_manager.save_config(settings)

    document = json.loads(config_manager.config_path.read_text(encoding="utf-8"))
    assert document["theme"] == "dark"
    assert document["open_tabs"] == ["one"]
    assert document["revision"] == settings.revision == 1


def test_concurrent_full_writes_are_serialized(tmp_path):
    config_manager = ConfigManager(config_dir=tmp_path)
    settings = AppSettings(theme="dark")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(config_manager.save_config, settings) for _ in range(2)]
        for future in futures:
            future.result()

    assert settings.revision == 2
    assert ConfigManager(config_dir=tmp_path).load_config().revision == 2


def test_recovery_notice_is_presented_to_user(tmp_path):
    original = tmp_path / "settings.json"
    quarantined = tmp_path / "settings.json.corrupt"
    config_manager = MagicMock()
    config_manager.recovery_notice = ConfigRecoveryNotice(
        original_path=original,
        quarantine_path=quarantined,
        category="malformed_json",
    )
    window = SimpleNamespace(config_manager=config_manager, _teardown_started=False)

    with patch.object(
        main_window_settings, "show_settings_recovery_warning"
    ) as show_warning:
        main_window_settings.show_recovery_notice(window)

    show_warning.assert_called_once_with(window, original, quarantined)
