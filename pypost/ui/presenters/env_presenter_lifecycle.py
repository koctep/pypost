"""Lifecycle coordination helpers for environment presentation."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from pypost.core.lifecycle import (
    TeardownResult,
    record_lifecycle_event,
    record_teardown_metrics,
    teardown_correlation_id,
)
from pypost.core.variable_name_validation import (
    validate_variable_name,
    validation_failure_reason,
)
from pypost.models.models import Environment

logger = logging.getLogger(__name__)
validation_logger = logging.getLogger("pypost.ui.presenters.env_presenter")

if TYPE_CHECKING:
    from pypost.ui.presenters.env_presenter import EnvPresenter


def begin_teardown(presenter: EnvPresenter) -> None:
    """Fence presenter callbacks and storage admission."""
    with presenter._lifecycle_lock:
        if presenter._teardown_result is None:
            presenter._teardown_started = True
            presenter._storage_gateway.begin_teardown()


def teardown(presenter: EnvPresenter, timeout_ms: int | None = None) -> TeardownResult:
    """Drain accepted gateway work under one bounded presenter deadline."""
    budget_ms = 5000 if timeout_ms is None else max(0, timeout_ms)
    with presenter._teardown_lock:
        if presenter._teardown_result is not None:
            return presenter._teardown_result
        started = time.monotonic()
        correlation_id = teardown_correlation_id(presenter)
        with presenter._lifecycle_lock:
            presenter._teardown_started = True
        logger.info(
            "lifecycle_teardown_started owner=env_presenter teardown_id=%s "
            "timeout_ms=%d",
            correlation_id,
            budget_ms,
        )
        gateway_result = presenter._storage_gateway.teardown(timeout_ms=budget_ms)
        presenter._teardown_result = TeardownResult(
            owner="env_presenter",
            outcome=gateway_result.outcome,
            elapsed_ms=int((time.monotonic() - started) * 1000),
            active_count=gateway_result.active_count,
            pending_count=gateway_result.pending_count,
            failure_kind=gateway_result.failure_kind,
            dispositions=gateway_result.dispositions,
        )
        logger.info(
            "lifecycle_teardown_completed owner=env_presenter teardown_id=%s "
            "outcome=%s elapsed_ms=%d deadline_ms=%d active_count=%d pending_count=%d",
            correlation_id,
            presenter._teardown_result.outcome,
            presenter._teardown_result.elapsed_ms,
            budget_ms,
            presenter._teardown_result.active_count,
            presenter._teardown_result.pending_count,
        )
        record_teardown_metrics(presenter, presenter._teardown_result, presenter._metrics)
        return presenter._teardown_result


def apply_loaded_environments(presenter: EnvPresenter, environments: list[Environment]) -> None:
    presenter._environments = environments
    logger.info("load_environments_completed count=%d", len(presenter._environments))
    presenter._env_selector.blockSignals(True)
    presenter._env_selector.clear()
    presenter._env_selector.addItem("No Environment", None)
    selected_index = 0
    for index, environment in enumerate(presenter._environments):
        presenter._env_selector.addItem(environment.name, environment)
        if presenter._settings.last_environment_id == environment.id:
            selected_index = index + 1
    presenter._env_selector.setCurrentIndex(selected_index)
    presenter._current_env_index = selected_index
    presenter._env_selector.blockSignals(False)
    if selected_index > 0:
        presenter._on_env_changed(selected_index)


def on_storage_load_completed(presenter: EnvPresenter, environments: list[Environment]) -> None:
    with presenter._lifecycle_lock:
        if presenter._admission_closed():
            logger.info(
                "lifecycle_late_delivery_ignored owner=env_presenter "
                "kind=load_completed teardown_id=%s",
                teardown_correlation_id(presenter),
            )
            record_lifecycle_event(
                presenter, "late_signal_suppressed", metrics=presenter._metrics
            )
            return
        apply_loaded_environments(presenter, environments)
        if presenter._pending_env_manager_refresh:
            presenter._pending_env_manager_refresh = False
            presenter._on_env_changed(presenter._env_selector.currentIndex())
        presenter.environments_loaded.emit()


def on_storage_save_outcome(presenter: EnvPresenter, sequence: object, outcome: str) -> None:
    if isinstance(sequence, int):
        presenter.environment_update_disposition.emit(sequence, outcome)


def on_storage_load_failed(presenter: EnvPresenter, error: object) -> None:
    with presenter._lifecycle_lock:
        if presenter._admission_closed():
            logger.info(
                "lifecycle_late_delivery_ignored owner=env_presenter "
                "kind=load_failed teardown_id=%s",
                teardown_correlation_id(presenter),
            )
            record_lifecycle_event(
                presenter, "late_signal_suppressed", metrics=presenter._metrics
            )
            return
        logger.error("storage_load_failed error=%s", error)
        apply_loaded_environments(presenter, [])
        presenter.environments_loaded.emit()


def on_storage_save_failed(presenter: EnvPresenter, error: object, show_error) -> None:
    with presenter._lifecycle_lock:
        if presenter._admission_closed():
            logger.info(
                "lifecycle_late_delivery_ignored owner=env_presenter "
                "kind=save_failed teardown_id=%s",
                teardown_correlation_id(presenter),
            )
            record_lifecycle_event(
                presenter, "late_signal_suppressed", metrics=presenter._metrics
            )
            return
        message = str(error) if error else "Failed to save environments."
        logger.error("storage_save_failed error=%s", message)
        show_error(presenter._widget, message)


def validate_variable(presenter: EnvPresenter, name: str) -> tuple[bool, str]:
    """Validate a manual environment key and record its outcome."""
    is_valid, error_msg = validate_variable_name(name)
    if is_valid:
        presenter._metrics.track_variable_validation("valid")
        return True, ""
    reason = validation_failure_reason(name)
    if reason:
        presenter._metrics.track_variable_validation_failure(reason)
    presenter._metrics.track_variable_validation("invalid")
    validation_logger.debug(
        "variable_name_validation_attempt name=%s valid=False error=%s",
        name,
        reason or "unknown",
    )
    return False, error_msg
