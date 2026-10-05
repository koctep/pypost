"""Failing repro and signal stress benchmark tests for PYPOST-1242.

Covers:
1. Idempotent signal wiring in wire_presenter_signals (repro defect: duplicate connections).
2. Rapid sequential switching burst stress (60 switches across 5 mock environments).
3. High-frequency variable update burst (120 rapid updates without queue deadlock).
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QWidget

from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.main_window_signals import wire_presenter_signals
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.ui.presenters.mcp_controls_presenter import McpControlsPresenter

pytestmark = pytest.mark.timeout(30)


@pytest.fixture(autouse=True)
def _prevent_blocking_dialogs():
    """Ensure message boxes never block test execution."""
    with patch("pypost.ui.presenters.env_presenter.show_no_environment_selected"), \
         patch("pypost.ui.presenters.env_presenter.show_invalid_variable_name_error"):
        yield


def _make_env(
    env_id: str,
    name: str,
    variables: dict[str, str] | None = None,
    enable_mcp: bool = False,
) -> Environment:
    return Environment(
        id=env_id,
        name=name,
        variables=variables or {},
        enable_mcp=enable_mcp,
    )


class _FakeStorage:
    def __init__(self, environments: list[Environment] | None = None) -> None:
        self._environments = environments or []
        self.saved: list[list[Environment]] = []

    def load_environments(self) -> list[Environment]:
        return list(self._environments)

    def save_environments(self, envs: list[Environment]) -> None:
        self.saved.append(list(envs))

    def serialize_environment_records(
        self,
        environments: list[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> list[dict]:
        return [env.model_dump(mode="json") for env in environments]


class _FakeConfigManager:
    def __init__(self) -> None:
        self.saved: list[AppSettings] = []

    def save_config(self, settings: AppSettings) -> None:
        self.saved.append(settings)


def _make_env_presenter(environments: list[Environment] | None = None) -> EnvPresenter:
    storage = _FakeStorage(environments)
    config = _FakeConfigManager()
    mcp = MagicMock()
    settings = AppSettings()
    metrics = MagicMock()
    return EnvPresenter(
        storage=storage,
        config_manager=config,
        mcp_manager=mcp,
        settings=settings,
        get_collections=lambda: [],
        metrics=metrics,
    )


class _DummyWindow:
    """Mock container representing MainWindow for signal wiring."""

    def __init__(self, env: EnvPresenter, mcp_controls: object) -> None:
        self.collections = MagicMock()
        self.tabs = MagicMock()
        self.env = env
        self.mcp_controls = mcp_controls
        self.history_panel = MagicMock()
        self.history_manager = MagicMock()
        self._status_bar = MagicMock()

    def statusBar(self) -> MagicMock:
        return self._status_bar


@pytest.mark.timeout(30)
def test_wire_presenter_signals_is_idempotent(qapp) -> None:
    """Calling wire_presenter_signals multiple times must not register duplicate connections."""
    env = _make_env("env_1", "Test Env")
    presenter = _make_env_presenter([env])
    try:
        presenter.load_environments()
        mcp_controls = MagicMock()
        window = _DummyWindow(presenter, mcp_controls)

        # Wire twice to test idempotency
        wire_presenter_signals(window)
        wire_presenter_signals(window)

        # Emit environment_selected signal
        presenter.environment_selected.emit(env)

        # In idempotent wiring, slot must be triggered exactly once, not twice
        assert mcp_controls.handle_environment_selected.call_count == 1, (
            f"Expected slot to be called exactly once, but got "
            f"{mcp_controls.handle_environment_selected.call_count} calls "
            f"(duplicate signal connections registered)"
        )
    finally:
        presenter.widget.deleteLater()


@pytest.mark.timeout(30)
def test_rapid_environment_switching_burst_stress(qapp) -> None:
    """Stress test: 60 sequential environment selections across 5 environments.

    Verifies final state convergence, bounded execution duration, and event
    queue draining via QCoreApplication.processEvents().
    """
    envs = [_make_env(f"env_{i}", f"Env {i}") for i in range(5)]
    presenter = _make_env_presenter(envs)
    dialog_parent = QWidget()
    try:
        presenter.load_environments()
        manager = MagicMock()
        manager.is_running.return_value = False
        settings = AppSettings()
        metrics = MagicMock()

        mcp_presenter = McpControlsPresenter(
            mcp_manager=manager,
            settings_provider=lambda: settings,
            get_collections=lambda: [],
            get_environments=lambda: envs,
            current_environment=lambda: None,
            metrics=metrics,
            dialog_parent=dialog_parent,
        )

        presenter.environment_selected.connect(
            mcp_presenter.handle_environment_selected
        )

        switch_count = 60
        start_time = time.perf_counter()

        for step in range(switch_count):
            env_index = (step % 5) + 1
            presenter._env_selector.setCurrentIndex(env_index)
            QCoreApplication.processEvents()

        elapsed = time.perf_counter() - start_time
        avg_latency_ms = (elapsed / switch_count) * 1000.0

        assert elapsed <= 2.0, f"Burst duration {elapsed:.3f}s exceeded 2.0s limit"
        assert avg_latency_ms <= 5.0, (
            f"Average latency {avg_latency_ms:.2f}ms exceeded 5.0ms guardrail"
        )

        # Final state convergence: step 59 % 5 = 4, index 5 corresponds to envs[4]
        expected_final_env = envs[4]
        assert mcp_presenter._active_environment == expected_final_env
        assert presenter._env_selector.currentData() == expected_final_env
    finally:
        presenter.widget.deleteLater()
        dialog_parent.deleteLater()


@pytest.mark.timeout(30)
def test_high_frequency_variable_update_burst(qapp) -> None:
    """Stress test: 120 rapid variable updates verifying non-blocking event pump."""
    env = _make_env("env_test", "Test Env", {"INITIAL": "0"})
    presenter = _make_env_presenter([env])
    try:
        presenter.load_environments()
        presenter._env_selector.setCurrentIndex(1)

        recorded_updates: list[str] = []
        presenter.environment_updated.connect(recorded_updates.append)

        update_count = 120
        start_time = time.perf_counter()
        latencies_ms: list[float] = []

        for step in range(update_count):
            step_start = time.perf_counter()
            presenter.on_env_update({f"KEY_{step}": f"VAL_{step}"})
            QCoreApplication.processEvents()
            latencies_ms.append((time.perf_counter() - step_start) * 1000.0)

        total_elapsed = time.perf_counter() - start_time
        peak_latency_ms = max(latencies_ms) if latencies_ms else 0.0

        assert len(recorded_updates) == update_count
        assert peak_latency_ms <= 50.0, (
            f"Peak latency {peak_latency_ms:.2f}ms exceeded 50.0ms threshold"
        )
        assert total_elapsed <= 2.0, (
            f"Total duration {total_elapsed:.3f}s exceeded 2.0s guardrail"
        )

        active_env = presenter._env_selector.currentData()
        assert isinstance(active_env, Environment)
        for step in range(update_count):
            assert active_env.variables.get(f"KEY_{step}") == f"VAL_{step}"
    finally:
        presenter.widget.deleteLater()
