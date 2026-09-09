"""Composition-root lifecycle coordination for MainWindow."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from pypost.core.alert_manager import AlertManager
from pypost.core.config_manager import ConfigPersistenceError
from pypost.core.encryption_config import resolve_encryption_enabled
from pypost.core.lifecycle import (
    TeardownResult,
    record_teardown_metrics,
    teardown_correlation_id,
)
from pypost.models.settings import AppSettings

if TYPE_CHECKING:
    from pypost.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def configure_env_update_consumer(window: MainWindow) -> None:
    """Install the sequenced handoff while retaining the legacy callback seam."""
    accepted = getattr(window.env, "accept_accepted_env_update", None)
    if callable(accepted):
        window.tabs.set_environment_update_consumer(accepted)
        return
    legacy = getattr(window.env, "on_env_update", None)
    if callable(legacy):
        window.tabs.set_environment_update_consumer(
            lambda variables, _sequence: legacy(variables)
        )


def maybe_complete_startup_restore(window: MainWindow) -> None:
    """Restore persisted UI state once both asynchronous startup loads finish."""
    if getattr(window, "_teardown_started", False):
        return
    if not (window._startup_collections_ready and window._startup_env_ready):
        return
    window.tabs.restore_tabs()
    window.collections.restore_tree_state()
    window.mcp_controller.start_enabled()
    window._ui_ready = True
    logger.info("main_window_ui_ready")


def teardown(window: MainWindow, timeout_ms: int | None = None) -> TeardownResult:
    """Fence UI admission, drain request side effects, then close child owners."""
    budget_ms = 5000 if timeout_ms is None else max(0, timeout_ms)
    lock = getattr(window, "_teardown_lock", None)
    if lock is None:
        lock = threading.Lock()
        window._teardown_lock = lock
    with lock:
        existing = getattr(window, "_teardown_result", None)
        if isinstance(existing, TeardownResult):
            return existing
        started = time.monotonic()
        correlation_id = teardown_correlation_id(window)
        window._teardown_started = True
        owners = [
            owner
            for owner in (
                getattr(window, "tabs", None),
                getattr(window, "collections", None),
                getattr(window, "history_panel", None),
                getattr(window, "history_manager", None),
                getattr(window, "env", None),
            )
            if owner is not None and callable(getattr(owner, "teardown", None))
        ]
        for owner in owners:
            setattr(owner, "_teardown_correlation_id", correlation_id)
        logger.info(
            "lifecycle_teardown_started owner=main_window teardown_id=%s "
            "timeout_ms=%d owner_count=%d",
            correlation_id,
            budget_ms,
            len(owners),
        )
        for owner in owners[:-1]:
            begin = getattr(owner, "begin_teardown", None)
            if callable(begin):
                begin()
        env = getattr(window, "env", None)
        begin_root = getattr(env, "begin_root_teardown", None)
        if callable(begin_root):
            begin_root()
        if not owners:
            window._teardown_result = TeardownResult(
                owner="main_window", outcome="success", elapsed_ms=0
            )
            logger.info(
                "lifecycle_teardown_completed owner=main_window teardown_id=%s "
                "outcome=success elapsed_ms=0 deadline_ms=%d active_count=0 "
                "pending_count=0",
                correlation_id,
                budget_ms,
            )
            record_teardown_metrics(
                window, window._teardown_result, getattr(window, "metrics", None)
            )
            return window._teardown_result

        results = []
        deadline = started + budget_ms / 1000
        for index, owner in enumerate(owners):
            if owner is env:
                drain = getattr(window.tabs, "drain_accepted_env_updates", None)
                consumer = getattr(env, "accept_accepted_env_update", None)
                if callable(drain) and callable(consumer):
                    drain(consumer, getattr(window.tabs, "_env_update_cutoff", None))
                begin = getattr(owner, "begin_teardown", None)
                if callable(begin):
                    begin()
            slots_left = len(owners) - index
            allocated = int(budget_ms * slots_left / len(owners))
            remaining = max(0, int((deadline - time.monotonic()) * 1000))
            owner_budget = min(allocated, remaining)
            owner_result = owner.teardown(timeout_ms=owner_budget)
            if isinstance(owner_result, bool):
                owner_result = TeardownResult(
                    owner="collections_presenter",
                    outcome="success" if owner_result else "incomplete",
                    elapsed_ms=0,
                    failure_kind=None if owner_result else "timeout",
                )
            results.append(owner_result)

        if any(result.outcome == "failed" for result in results):
            outcome, failure_kind = "failed", "owner_failure"
        elif any(result.outcome == "incomplete" for result in results):
            outcome, failure_kind = "incomplete", "timeout"
        else:
            outcome, failure_kind = "success", None
        window._teardown_result = TeardownResult(
            owner="main_window",
            outcome=outcome,
            elapsed_ms=int((time.monotonic() - started) * 1000),
            active_count=sum(getattr(result, "active_count", 0) for result in results),
            pending_count=sum(getattr(result, "pending_count", 0) for result in results),
            failure_kind=failure_kind,
        )
        logger.info(
            "lifecycle_teardown_completed owner=main_window teardown_id=%s "
            "outcome=%s elapsed_ms=%d deadline_ms=%d active_count=%d pending_count=%d",
            correlation_id,
            outcome,
            window._teardown_result.elapsed_ms,
            budget_ms,
            window._teardown_result.active_count,
            window._teardown_result.pending_count,
        )
        record_teardown_metrics(
            window, window._teardown_result, getattr(window, "metrics", None)
        )
        return window._teardown_result


def shutdown_for_exit(
    window: MainWindow,
    encryption_enabled_resolver: Callable[[AppSettings | None], bool] = resolve_encryption_enabled,
) -> TeardownResult:
    """Run the bounded application shutdown sequence once."""
    existing = getattr(window, "_teardown_result", None)
    if isinstance(existing, TeardownResult):
        return existing
    try:
        window.state_manager.flush_pending_save()
    except ConfigPersistenceError:
        logger.error("lifecycle_shutdown_blocked reason=settings_save_failed")
        return TeardownResult(
            owner="main_window",
            outcome="failed",
            elapsed_ms=0,
            failure_kind="settings_save_failed",
        )
    result = window.teardown(timeout_ms=5000)
    if result.outcome != "success":
        return result
    if encryption_enabled_resolver(window.settings):
        window.env.wait_storage_idle(timeout_ms=0)
    return result


def close_event(window: MainWindow, event) -> None:
    result = window._shutdown_for_exit()
    if result.outcome == "success":
        event.accept()
    else:
        event.ignore()


def handle_exit(window: MainWindow) -> None:
    result = window._shutdown_for_exit()
    if result.outcome == "success":
        from PySide6.QtWidgets import QApplication

        QApplication.instance().quit()


def open_library_manager(window: MainWindow) -> None:
    if not window._teardown_started:
        from pypost.ui.dialogs.library_dialogs import LibraryManagerDialog

        LibraryManagerDialog(parent=window).exec()


def show_hotkeys(window: MainWindow) -> None:
    if not window._teardown_started:
        from pypost.ui.dialogs.hotkeys_dialog import HotkeysDialog

        HotkeysDialog(window).exec()


def show_about(window: MainWindow) -> None:
    if not window._teardown_started:
        from pypost.ui.dialogs.about_dialog import AboutDialog

        AboutDialog(window).exec()


def alert_settings_changed(previous: AppSettings, updated: AppSettings) -> bool:
    return (
        previous.alert_log_path != updated.alert_log_path
        or previous.alert_webhook_url != updated.alert_webhook_url
        or previous.alert_webhook_auth_header != updated.alert_webhook_auth_header
    )


def reload_alert_manager(
    window: MainWindow,
    alert_manager_factory: Callable[..., AlertManager],
) -> None:
    if window._alert_manager is not None:
        window._alert_manager.close()
    override = getattr(window, "_alert_log_path_override", None)
    fallback = getattr(window, "_default_alert_log_path", None)
    log_path = (
        override
        or (Path(window.settings.alert_log_path) if window.settings.alert_log_path else None)
        or fallback
    )
    window._alert_manager = alert_manager_factory(
        log_path=log_path,
        webhook_url=window.settings.alert_webhook_url,
        webhook_auth_header=window.settings.alert_webhook_auth_header,
    )
    window.tabs.set_alert_manager(window._alert_manager)
    logger.info(
        "alert_manager_reloaded log_path=%s webhook_url_set=%s",
        log_path,
        bool(window.settings.alert_webhook_url),
    )
