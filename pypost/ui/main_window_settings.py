"""Settings-dialog transaction and persistence feedback for ``MainWindow``."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QDialog

from pypost.core.config_manager import ConfigPersistenceError
from pypost.models.settings import AppSettings, update_settings_snapshot
from pypost.ui.collection_item_dialogs import (
    show_settings_recovery_warning,
    show_settings_save_failed,
)
from pypost.ui.dialogs.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


def apply_settings(window, settings: AppSettings) -> None:
    if getattr(window, "_teardown_started", False):
        return
    app = QApplication.instance()
    if app:
        window.style_manager.apply_appearance(
            app, theme=settings.theme, font_size=settings.font_size
        )
    window.tabs.apply_settings(settings)
    window.env.apply_settings(settings)


def open_settings(
    window,
    dialog_factory: Callable[..., SettingsDialog] = SettingsDialog,
) -> None:
    if window._teardown_started:
        return
    dialog = dialog_factory(window.settings, window, storage=window.storage)
    accepted = False
    try:
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_settings = dialog.get_settings()
        if new_settings is None:
            return
        previous_settings = window.settings.model_copy(deep=True)
        metrics_changed = (
            previous_settings.metrics_host != new_settings.metrics_host
            or previous_settings.metrics_port != new_settings.metrics_port
        )
        alert_changed = window._alert_settings_changed(previous_settings, new_settings)
        if window._teardown_started:
            return
        try:
            window.config_manager.save_config(new_settings)
        except ConfigPersistenceError as exc:
            show_settings_save_failed(window, str(exc))
            return

        # Every presenter and StateManager retains this object's identity.
        update_settings_snapshot(window.settings, new_settings)
        accepted = True
        window.env.wait_storage_idle()
        window.storage.apply_encryption_settings(window.settings)
        window.apply_settings(window.settings)
        if alert_changed:
            window._reload_alert_manager()
        if metrics_changed:
            logger.info(
                "metrics_server_restarting host=%s port=%d",
                window.settings.metrics_host,
                window.settings.metrics_port,
            )
            window.metrics.restart_server(
                window.settings.metrics_host,
                window.settings.metrics_port,
            )
        logger.info(
            "settings_applied font_size=%d indent_size=%d request_timeout=%d "
            "env_encryption_enabled=%s env_encryption_key_source=%s",
            window.settings.font_size,
            window.settings.indent_size,
            window.settings.request_timeout,
            window.settings.env_encryption_enabled,
            window.settings.env_encryption_key_source,
        )
    finally:
        dialog.cleanup()
        dialog.deleteLater()
        QCoreApplication.processEvents()
    if accepted and not window._teardown_started:
        window.env.reload_current_env()


def show_persistence_failure(window, message: str) -> None:
    if not getattr(window, "_teardown_started", False):
        show_settings_save_failed(window, message)


def show_recovery_notice(window) -> None:
    notice = window.config_manager.recovery_notice
    if notice is None or getattr(window, "_teardown_started", False):
        return
    show_settings_recovery_warning(
        window,
        notice.original_path,
        notice.quarantine_path,
    )
