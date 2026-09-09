"""Composition-root ownership, rollback, and repeated-session regressions."""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent

from pypost.agent.lifecycle import AgentAppSession
from pypost.core.lifecycle import ApplicationLifecycle, TeardownResult
from pypost.core.qt.collection_storage_gateway import CollectionStorageGateway
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(120)


def test_application_lifecycle_is_lifo_idempotent_and_best_effort() -> None:
    events: list[str] = []
    lifecycle = ApplicationLifecycle()
    lifecycle.own("first", lambda: events.append("first"))

    def fail_second() -> None:
        events.append("second")
        raise RuntimeError("cleanup failure")

    lifecycle.own("second", fail_second)
    lifecycle.own("third", lambda: events.append("third"))

    first_result = lifecycle.shutdown()
    second_result = lifecycle.shutdown()

    assert events == ["third", "second", "first"]
    assert first_result == second_result
    assert len(first_result) == 1
    assert first_result[0].owner == "second"


def test_collection_startup_loader_fences_late_delivery(qapp) -> None:
    release = threading.Event()
    storage = MagicMock()

    def load_collections() -> list[object]:
        release.wait(2.0)
        return []

    storage.load_collections.side_effect = load_collections
    gateway = CollectionStorageGateway(storage)
    delivered = MagicMock()
    gateway.load_completed.connect(delivered)
    gateway.load_async()

    result = gateway.teardown(timeout_ms=0)
    assert result.outcome == "incomplete"

    release.set()
    worker = gateway._worker
    assert worker is not None
    assert worker.wait(2000)
    QCoreApplication.processEvents()
    delivered.assert_not_called()


_COMPOSITION_STEPS = (
    "config_manager",
    "load_config",
    "state_manager",
    "metrics_manager",
    "metrics_start",
    "template_service",
    "alert_manager",
    "history_manager",
    "storage_manager",
    "request_manager",
    "mcp_manager",
    "main_window",
    "initial_loads",
)


@pytest.mark.parametrize("failure_step", _COMPOSITION_STEPS)
def test_compose_failure_rolls_back_every_acquired_owner(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure_step: str,
) -> None:
    import pypost.main as main_module

    events: list[str] = []
    settings = AppSettings()
    config = MagicMock()
    metrics = MagicMock()
    alert = MagicMock()
    window = MagicMock()
    window._alert_manager = alert
    window.mcp_controller.registry = MagicMock()
    window._shutdown_for_exit.side_effect = lambda: (
        events.append("main_window")
        or TeardownResult("main_window", "success", 0)
    )
    metrics.stop_server.side_effect = lambda: events.append("metrics_server")
    alert.close.side_effect = lambda: events.append("alert_manager")

    def build(step: str, value: object):
        def factory(*_args: object, **_kwargs: object) -> object:
            if failure_step == step:
                raise RuntimeError(f"failed at {step}")
            return value

        return factory

    config.load_config.side_effect = (
        RuntimeError("failed at load_config")
        if failure_step == "load_config"
        else None
    )
    if failure_step != "load_config":
        config.load_config.return_value = settings
    metrics.start_server.side_effect = (
        RuntimeError("failed at metrics_start")
        if failure_step == "metrics_start"
        else None
    )
    window.start_initial_loads.side_effect = (
        RuntimeError("failed at initial_loads")
        if failure_step == "initial_loads"
        else None
    )

    replacements = {
        "ConfigManager": build("config_manager", config),
        "StateManager": build("state_manager", MagicMock(settings=settings)),
        "MetricsManager": build("metrics_manager", metrics),
        "TemplateService": build("template_service", MagicMock()),
        "AlertManager": build("alert_manager", alert),
        "HistoryManager": build("history_manager", MagicMock()),
        "StorageManager": build("storage_manager", MagicMock()),
        "RequestManager": build("request_manager", MagicMock()),
        "MCPServerManager": build("mcp_manager", MagicMock()),
        "MainWindow": build("main_window", window),
    }
    for name, replacement in replacements.items():
        monkeypatch.setattr(main_module, name, replacement)

    with pytest.raises(RuntimeError, match=f"failed at {failure_step}"):
        main_module.compose_app(
            config_dir=tmp_path / "config",
            data_dir=tmp_path / "data",
            apply_log_level=False,
        )

    failure_index = _COMPOSITION_STEPS.index(failure_step)
    expected: list[str] = []
    if failure_index > _COMPOSITION_STEPS.index("main_window"):
        expected.append("main_window")
    if failure_index > _COMPOSITION_STEPS.index("alert_manager"):
        expected.append("alert_manager")
    if failure_index > _COMPOSITION_STEPS.index("metrics_manager"):
        expected.append("metrics_server")
    assert events == expected


def test_composed_app_owns_reloaded_alert_attach_window_and_metrics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import pypost.main as main_module

    events: list[str] = []
    settings = AppSettings()
    config = MagicMock()
    config.load_config.return_value = settings
    metrics = MagicMock()
    metrics.stop_server.side_effect = lambda: events.append("metrics_server")
    original_alert = MagicMock()
    reloaded_alert = MagicMock()
    reloaded_alert.close.side_effect = lambda: events.append("alert_manager")
    registry = MagicMock()
    window = MagicMock()
    window._alert_manager = original_alert
    window.mcp_controller.registry = registry
    window._shutdown_for_exit.side_effect = lambda: (
        events.append("main_window")
        or TeardownResult("main_window", "success", 0)
    )

    monkeypatch.setattr(main_module, "ConfigManager", lambda **_kwargs: config)
    monkeypatch.setattr(
        main_module, "StateManager", lambda *_args: MagicMock(settings=settings)
    )
    monkeypatch.setattr(main_module, "MetricsManager", lambda: metrics)
    monkeypatch.setattr(main_module, "TemplateService", lambda **_kwargs: MagicMock())
    monkeypatch.setattr(main_module, "AlertManager", lambda **_kwargs: original_alert)
    monkeypatch.setattr(main_module, "HistoryManager", lambda **_kwargs: MagicMock())
    monkeypatch.setattr(main_module, "StorageManager", lambda **_kwargs: MagicMock())
    monkeypatch.setattr(main_module, "RequestManager", lambda *_args, **_kwargs: MagicMock())
    monkeypatch.setattr(main_module, "MCPServerManager", lambda **_kwargs: MagicMock())
    monkeypatch.setattr(main_module, "MainWindow", lambda **_kwargs: window)

    composed = main_module.compose_app(
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        apply_log_level=False,
    )
    attach = MagicMock()
    attach.stop.side_effect = lambda: events.append("attach_host")
    composed.own_attach_host(attach)
    window._alert_manager = reloaded_alert

    assert composed.alert_manager is reloaded_alert
    assert composed.lifecycle_owner_names == (
        "metrics_server",
        "alert_manager",
        "main_window",
        "attach_host",
    )
    assert composed.shutdown() == ()
    assert composed.shutdown() == ()
    assert events == ["attach_host", "main_window", "alert_manager", "metrics_server"]
    original_alert.close.assert_not_called()


def test_data_dir_is_also_the_default_alert_log_boundary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import pypost.main as main_module

    settings = AppSettings()
    config = MagicMock()
    config.load_config.return_value = settings
    alert_factory = MagicMock(side_effect=RuntimeError("stop after alert path resolution"))
    monkeypatch.setattr(main_module, "ConfigManager", lambda **_kwargs: config)
    monkeypatch.setattr(
        main_module, "StateManager", lambda *_args: MagicMock(settings=settings)
    )
    monkeypatch.setattr(main_module, "MetricsManager", lambda: MagicMock())
    monkeypatch.setattr(main_module, "TemplateService", lambda **_kwargs: MagicMock())
    monkeypatch.setattr(main_module, "AlertManager", alert_factory)

    data_dir = tmp_path / "isolated-data"
    with pytest.raises(RuntimeError, match="stop after alert"):
        main_module.compose_app(data_dir=data_dir, apply_log_level=False)

    assert alert_factory.call_args.kwargs["log_path"] == data_dir / "pypost-alerts.log"


def test_desktop_attach_start_failure_uses_shared_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pypost.agent.attach_ipc as attach_module
    import pypost.main as main_module

    application = MagicMock()
    monkeypatch.setattr(main_module, "QApplication", MagicMock(return_value=application))
    composed = MagicMock()
    monkeypatch.setattr(main_module, "compose_app", MagicMock(return_value=composed))
    host = MagicMock(endpoint="/tmp/test-attach.sock")
    host.start.side_effect = OSError("bind failed")
    monkeypatch.setattr(attach_module, "AgentUiAttachHost", MagicMock(return_value=host))

    with pytest.raises(OSError, match="bind failed"):
        main_module.main()

    composed.own_attach_host.assert_called_once_with(host)
    composed.shutdown.assert_called_once_with()
    application.exec.assert_not_called()


def test_agent_shutdown_delegates_to_composed_lifecycle_once() -> None:
    session = AgentAppSession()
    composed = MagicMock()
    composed.shutdown.return_value = ()
    session._composed = composed

    session.shutdown()
    session.shutdown()

    composed.shutdown.assert_called_once_with()


@pytest.mark.timeout(120)
@pytest.mark.agent_e2e
def test_repeated_agent_sessions_leave_no_handlers_fds_widgets_or_threads(qapp) -> None:
    def fd_targets() -> list[str]:
        targets: list[str] = []
        for fd in os.listdir("/proc/self/fd"):
            try:
                targets.append(os.readlink(f"/proc/self/fd/{fd}"))
            except FileNotFoundError:
                continue
        return sorted(targets)

    # Qt/asyncio lazily allocate process-wide dispatcher descriptors on the
    # first real composition. Warm those singletons before measuring growth.
    with AgentAppSession(offscreen=True, ready_timeout=30.0):
        pass
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()

    baseline_threads = set(threading.enumerate())
    baseline_widgets = set(qapp.topLevelWidgets())
    baseline_fd_targets = fd_targets()

    for _index in range(3):
        with AgentAppSession(offscreen=True, ready_timeout=30.0):
            pass
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()

        leaked_handlers = [
            handler
            for name, candidate in logging.Logger.manager.loggerDict.items()
            if name.startswith("pypost.alerts.") and isinstance(candidate, logging.Logger)
            for handler in candidate.handlers
        ]
        assert leaked_handlers == []
        assert set(threading.enumerate()) <= baseline_threads
        assert set(qapp.topLevelWidgets()) <= baseline_widgets
        current_fd_targets = fd_targets()
        assert len(current_fd_targets) <= len(baseline_fd_targets), (
            baseline_fd_targets,
            current_fd_targets,
        )
