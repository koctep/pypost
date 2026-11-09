"""Red acceptance tests for isolated MCP worker memory ceilings and admission (PYPOST-1469).

Architecture: ai-tasks/PYPOST-1469/20-architecture.md § Mandatory — Failing Repro

Covers:
1. McpResourceLimitsPolicy settings defaults, bounds validation, and cross-field constraints
2. Default policy unlimited allows spawns without rejection
3. Spawn admission worker count limit rejects excess spawns
4. Spawn admission total RSS budget rejects excess spawns
5. Soft memory limit emits warning without killing worker
6. Hard memory limit escalates and terminates runaway worker
7. Admission exhaustion halts auto-restart backoff cycle
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

import pypost.core.mcp_process_supervisor as supervisor_mod
import pypost.models.settings as settings_mod
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.mcp_server_runner import ProcessServerRunner
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import AppSettings, McpServerConfiguration
from tests.helpers.port_allocation import reserve_ephemeral_ports

pytestmark = pytest.mark.timeout(60)

_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


def _require_resource_limits_policy_cls() -> Any:
    """Return McpResourceLimitsPolicy from pypost.models.settings or fail red."""
    policy_cls = getattr(settings_mod, "McpResourceLimitsPolicy", None)
    assert policy_cls is not None, (
        "McpResourceLimitsPolicy is not defined in pypost.models.settings"
    )
    return policy_cls


def _require_admission_error_cls() -> Any:
    """Return McpAdmissionError from pypost.core.mcp_process_supervisor or fail red."""
    err_cls = getattr(supervisor_mod, "McpAdmissionError", None)
    assert err_cls is not None, (
        "McpAdmissionError is not defined in pypost.core.mcp_process_supervisor"
    )
    return err_cls


def wait_until(
    predicate: Callable[[], bool],
    *,
    timeout: float = 5.0,
    interval: float = 0.03,
    description: str = "condition",
) -> None:
    """Poll predicate until it returns True or timeout expires."""
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
            last_exc = None
        except Exception as exc:  # pragma: no cover - transient poll error
            last_exc = exc
        time.sleep(interval)
    if last_exc is not None:
        raise AssertionError(
            f"Timed out waiting for {description} after {timeout}s: {last_exc}"
        ) from last_exc
    assert predicate(), f"Timed out waiting for {description} after {timeout}s"


def _make_dummy_collection_and_env(name: str = "test") -> tuple[Collection, Environment]:
    collection = Collection(
        id=f"col-{name}",
        requests=[
            RequestData(
                id=f"req-{name}",
                name="default_tool",
                method="GET",
                url=f"http://127.0.0.1/{name}",
                expose_as_mcp=True,
            )
        ],
    )
    env = Environment(id=f"env-{name}", variables={})
    return collection, env


@pytest.mark.timeout(20)
def test_resource_limits_policy_settings_defaults_and_validation() -> None:
    """McpResourceLimitsPolicy defaults, bounds validation, and AppSettings wiring."""
    policy_cls = _require_resource_limits_policy_cls()

    # Default values check
    default_policy = policy_cls()
    assert default_policy.max_process_workers == 0
    assert default_policy.max_total_rss_mb == pytest.approx(0.0)
    assert default_policy.soft_memory_limit_mb == pytest.approx(0.0)
    assert default_policy.hard_memory_limit_mb == pytest.approx(0.0)
    assert default_policy.memory_sample_interval_s == pytest.approx(1.0)
    assert default_policy.default_worker_rss_estimate_mb == pytest.approx(50.0)

    # Valid custom configuration
    custom_policy = policy_cls(
        max_process_workers=4,
        max_total_rss_mb=500.0,
        soft_memory_limit_mb=80.0,
        hard_memory_limit_mb=120.0,
        memory_sample_interval_s=0.5,
        default_worker_rss_estimate_mb=60.0,
    )
    assert custom_policy.max_process_workers == 4
    assert custom_policy.max_total_rss_mb == pytest.approx(500.0)
    assert custom_policy.soft_memory_limit_mb == pytest.approx(80.0)
    assert custom_policy.hard_memory_limit_mb == pytest.approx(120.0)
    assert custom_policy.memory_sample_interval_s == pytest.approx(0.5)
    assert custom_policy.default_worker_rss_estimate_mb == pytest.approx(60.0)

    # Validation bounds: negative and out-of-range checks
    with pytest.raises(ValidationError):
        policy_cls(max_process_workers=-1)
    with pytest.raises(ValidationError):
        policy_cls(max_process_workers=101)
    with pytest.raises(ValidationError):
        policy_cls(max_total_rss_mb=-1.0)
    with pytest.raises(ValidationError):
        policy_cls(soft_memory_limit_mb=-1.0)
    with pytest.raises(ValidationError):
        policy_cls(hard_memory_limit_mb=-1.0)
    with pytest.raises(ValidationError):
        policy_cls(memory_sample_interval_s=0.0)
    with pytest.raises(ValidationError):
        policy_cls(memory_sample_interval_s=-0.5)
    with pytest.raises(ValidationError):
        policy_cls(default_worker_rss_estimate_mb=-10.0)

    # Cross-field validation: hard_memory_limit_mb >= soft_memory_limit_mb when both > 0
    with pytest.raises(ValidationError):
        policy_cls(soft_memory_limit_mb=100.0, hard_memory_limit_mb=50.0)

    # AppSettings wiring and defaults
    settings = AppSettings()
    assert hasattr(settings, "mcp_resource_limits")
    assert isinstance(settings.mcp_resource_limits, policy_cls)
    assert settings.mcp_resource_limits.max_process_workers == 0

    # Serialization and round-trip
    custom_settings = AppSettings(
        mcp_execution_mode="process",
        mcp_resource_limits=custom_policy,
    )
    assert custom_settings.mcp_resource_limits == custom_policy
    payload = custom_settings.model_dump()
    assert "mcp_resource_limits" in payload
    restored = AppSettings.model_validate(payload)
    assert restored.mcp_resource_limits == custom_policy


@pytest.mark.timeout(30)
def test_default_policy_unlimited_allows_spawns_without_rejection() -> None:
    """Default policy with zero limits allows spawning workers without admission rejection."""
    policy_cls = _require_resource_limits_policy_cls()
    policy = policy_cls()
    assert policy.max_process_workers == 0
    assert policy.max_total_rss_mb == pytest.approx(0.0)

    col, env = _make_dummy_collection_and_env("unlimited")
    with reserve_ephemeral_ports(2) as ports:
        port1, port2 = ports[0], ports[1]
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            resource_limits=policy,
        )
        try:
            for srv_id, port in (("srv-unlim-1", port1), ("srv-unlim-2", port2)):
                registry.upsert(
                    McpServerConfiguration(
                        id=srv_id,
                        host="127.0.0.1",
                        port=port,
                        collection_id=col.id,
                        environment_id=env.id,
                        enabled=True,
                    )
                )
                ports.release()
                registry.start(srv_id)
                assert registry.wait_for_state(srv_id, "running", timeout=15.0)

            # Both servers successfully running
            assert registry.status("srv-unlim-1").state == "running"
            assert registry.status("srv-unlim-2").state == "running"
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_spawn_admission_worker_count_limit_rejects_excess_spawns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Configured max_process_workers rejects excess spawns while protecting running peers."""
    policy_cls = _require_resource_limits_policy_cls()
    admission_err_cls = _require_admission_error_cls()

    policy = policy_cls(max_process_workers=2)
    col, env = _make_dummy_collection_and_env("worker-cap")

    with reserve_ephemeral_ports(3) as ports:
        port1, port2, port3 = ports[0], ports[1], ports[2]
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            resource_limits=policy,
        )
        try:
            # Spawn worker 1 and worker 2 (reaching capacity)
            for srv_id, port in (("srv-cap-1", port1), ("srv-cap-2", port2)):
                registry.upsert(
                    McpServerConfiguration(
                        id=srv_id,
                        host="127.0.0.1",
                        port=port,
                        collection_id=col.id,
                        environment_id=env.id,
                        enabled=True,
                    )
                )
                ports.release()
                registry.start(srv_id)
                assert registry.wait_for_state(srv_id, "running", timeout=15.0)

            # Attempting to spawn 3rd worker exceeds worker cap
            registry.upsert(
                McpServerConfiguration(
                    id="srv-cap-3",
                    host="127.0.0.1",
                    port=port3,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )

            # Registry start must fail gracefully to "failed" with admission diagnostic
            with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_process_supervisor"):
                registry.start("srv-cap-3")
                assert registry.wait_for_state("srv-cap-3", "failed", timeout=5.0)
            status_3 = registry.status("srv-cap-3")
            msg = status_3.message.lower()
            assert "admission" in msg or "limit" in msg or "worker" in msg

            # Direct supervisor call must raise McpAdmissionError and emit warning log
            supervisor = registry._process_supervisor
            assert supervisor is not None
            with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_process_supervisor"):
                with pytest.raises(admission_err_cls) as exc_info:
                    supervisor.spawn_worker(
                        "direct-overflow",
                        host="127.0.0.1",
                        port=port3,
                        tools=[],
                        variables={},
                        hidden_keys=set(),
                        overridable_keys=set(),
                    )
            assert (
                "worker" in str(exc_info.value).lower()
                or "admission" in str(exc_info.value).lower()
            )
            rejected_records = [
                r for r in caplog.records
                if "mcp_worker_spawn_admission_rejected" in r.message
            ]
            assert len(rejected_records) >= 1
            assert any("srv-cap-3" in r.message for r in rejected_records)

            # Running workers remain healthy and untouched
            assert registry.status("srv-cap-1").state == "running"
            assert registry.status("srv-cap-2").state == "running"

            # Stopping 1 worker frees capacity
            registry.stop("srv-cap-1")
            assert registry.wait_for_state("srv-cap-1", "stopped", timeout=5.0)

            # Now starting 3rd worker succeeds
            registry.start("srv-cap-3")
            assert registry.wait_for_state("srv-cap-3", "running", timeout=15.0)
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_spawn_admission_total_rss_budget_rejects_excess_spawns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Configured max_total_rss_mb rejects spawn when aggregate memory budget is exceeded."""
    policy_cls = _require_resource_limits_policy_cls()
    admission_err_cls = _require_admission_error_cls()

    # Budget: 120 MB total, baseline estimate: 50 MB per worker.
    # Worker 1: 50 MB (<= 120 MB) -> allowed
    # Worker 2: 100 MB (<= 120 MB) -> allowed
    # Worker 3: 150 MB (> 120 MB) -> rejected!
    policy = policy_cls(
        max_total_rss_mb=120.0,
        default_worker_rss_estimate_mb=50.0,
    )
    col, env = _make_dummy_collection_and_env("rss-budget")

    with reserve_ephemeral_ports(3) as ports:
        port1, port2, port3 = ports[0], ports[1], ports[2]
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            resource_limits=policy,
        )
        try:
            for srv_id, port in (("srv-rss-1", port1), ("srv-rss-2", port2)):
                registry.upsert(
                    McpServerConfiguration(
                        id=srv_id,
                        host="127.0.0.1",
                        port=port,
                        collection_id=col.id,
                        environment_id=env.id,
                        enabled=True,
                    )
                )
                ports.release()
                registry.start(srv_id)
                assert registry.wait_for_state(srv_id, "running", timeout=15.0)

            # Spawning 3rd worker exceeds 120 MB aggregate RSS budget
            supervisor = registry._process_supervisor
            assert supervisor is not None
            with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_process_supervisor"):
                with pytest.raises(admission_err_cls) as exc_info:
                    supervisor.spawn_worker(
                        "srv-rss-3",
                        host="127.0.0.1",
                        port=port3,
                        tools=[],
                        variables={},
                        hidden_keys=set(),
                        overridable_keys=set(),
                    )
            err_msg = str(exc_info.value).lower()
            assert "memory" in err_msg or "rss" in err_msg or "budget" in err_msg

            rejected_records = [
                r for r in caplog.records
                if "mcp_worker_spawn_admission_rejected" in r.message
                and "srv-rss-3" in r.message
            ]
            assert len(rejected_records) >= 1
            assert rejected_records[0].levelno == logging.WARNING

            # Existing running workers continue operating without disruption
            assert registry.status("srv-rss-1").state == "running"
            assert registry.status("srv-rss-2").state == "running"
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_soft_memory_limit_emits_warning_without_killing_worker(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Soft memory threshold breach logs secret-safe warning without interrupting worker."""
    policy_cls = _require_resource_limits_policy_cls()
    policy = policy_cls(
        soft_memory_limit_mb=80.0,
        hard_memory_limit_mb=200.0,
        memory_sample_interval_s=0.05,
    )
    col, env = _make_dummy_collection_and_env("soft-mem")

    # Injected sampler reporting simulated 95 MB resident memory (> 80 MB soft limit)
    simulated_rss = 95.0

    def mock_sampler(pid: int) -> float:
        assert pid > 0
        return simulated_rss

    with reserve_ephemeral_ports(1) as ports:
        port1 = ports[0]
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            resource_limits=policy,
        )
        try:
            # Inject sampler into supervisor
            if registry._process_supervisor is not None:
                registry._process_supervisor._memory_sampler = mock_sampler

            registry.upsert(
                McpServerConfiguration(
                    id="srv-soft",
                    host="127.0.0.1",
                    port=port1,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )

            with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_process_supervisor"):
                ports.release()
                registry.start("srv-soft")
                assert registry.wait_for_state("srv-soft", "running", timeout=15.0)

                # Wait for periodic monitor loop to sample memory and emit warning
                wait_until(
                    lambda: any(
                        "mcp_worker_memory_warning" in r.message for r in caplog.records
                    ),
                    timeout=5.0,
                    description="soft memory ceiling warning log",
                )

            # Worker remains in running state without interruption
            assert registry.status("srv-soft").state == "running"
            runner = registry.runner_for("srv-soft")
            assert isinstance(runner, ProcessServerRunner)
            assert runner.is_running()

            # Secret-safety check on log records
            warning_records = [
                r for r in caplog.records if "mcp_worker_memory_warning" in r.message
            ]
            assert len(warning_records) >= 1
            record_msg = warning_records[0].message
            assert "srv-soft" in record_msg
            assert "password" not in record_msg.lower()
            assert "secret" not in record_msg.lower()
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_hard_memory_limit_escalates_and_terminates_runaway_worker(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Hard memory threshold breach terminates runaway worker while protecting peer workers."""
    policy_cls = _require_resource_limits_policy_cls()
    policy = policy_cls(
        soft_memory_limit_mb=50.0,
        hard_memory_limit_mb=120.0,
        memory_sample_interval_s=0.05,
    )
    col, env = _make_dummy_collection_and_env("hard-mem")

    with reserve_ephemeral_ports(2) as ports:
        port_healthy, port_runaway = ports[0], ports[1]
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            resource_limits=policy,
        )
        try:
            # Map PIDs to simulated RSS values: runaway exceeds hard limit
            rss_map: dict[int, float] = {}

            def mock_sampler(pid: int) -> float:
                return rss_map.get(pid, 40.0)

            registry.upsert(
                McpServerConfiguration(
                    id="srv-healthy",
                    host="127.0.0.1",
                    port=port_healthy,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )
            registry.upsert(
                McpServerConfiguration(
                    id="srv-runaway",
                    host="127.0.0.1",
                    port=port_runaway,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )

            # Start healthy worker
            ports.release()
            registry.start("srv-healthy")
            assert registry.wait_for_state("srv-healthy", "running", timeout=15.0)
            runner_healthy = registry.runner_for("srv-healthy")
            assert isinstance(runner_healthy, ProcessServerRunner)
            healthy_pid = runner_healthy.supervisor._workers["srv-healthy"].process.pid
            rss_map[healthy_pid] = 40.0

            # Inject sampler
            runner_healthy.supervisor._memory_sampler = mock_sampler

            # Start runaway worker and set its RSS above hard ceiling (150 MB > 120 MB)
            with caplog.at_level(logging.ERROR, logger="pypost.core.mcp_process_supervisor"):
                registry.start("srv-runaway")
                assert registry.wait_for_state("srv-runaway", "running", timeout=15.0)
                runner_runaway = registry.runner_for("srv-runaway")
                assert isinstance(runner_runaway, ProcessServerRunner)
                runaway_pid = runner_runaway.supervisor._workers["srv-runaway"].process.pid
                rss_map[runaway_pid] = 150.0

                # Runaway worker must be terminated and marked failed
                assert registry.wait_for_state("srv-runaway", "failed", timeout=10.0)

                # Supervisor must log mcp_worker_memory_exceeded error
                wait_until(
                    lambda: any(
                        "mcp_worker_memory_exceeded" in r.message for r in caplog.records
                    ),
                    timeout=5.0,
                    description="hard memory ceiling error log",
                )

            # Peer healthy worker remains running and intact
            assert registry.status("srv-healthy").state == "running"
            assert runner_healthy.is_running()

            # Runaway worker is terminated and dead
            assert not runner_runaway.is_running()
            assert "memory" in registry.status("srv-runaway").message.lower()
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_admission_exhaustion_halts_autorestart_backoff_cycle(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Admission exhaustion during auto-restart cancels retries and halts recovery loop."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    policy_cls = _require_resource_limits_policy_cls()
    restart_policy_cls = getattr(settings_mod, "McpWorkerRestartPolicy", None)
    assert restart_policy_cls is not None

    limits_policy = policy_cls(max_process_workers=1)
    restart_policy = restart_policy_cls(
        enabled=True,
        max_retries=3,
        initial_backoff_s=0.1,
        max_backoff_s=0.4,
    )
    col, env = _make_dummy_collection_and_env("restart-halt")

    with reserve_ephemeral_ports(2) as ports:
        port1 = ports[0]
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            resource_limits=limits_policy,
            restart_policy=restart_policy,
        )
        try:
            registry.upsert(
                McpServerConfiguration(
                    id="srv-restart-halt",
                    host="127.0.0.1",
                    port=port1,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )
            ports.release()
            registry.start("srv-restart-halt")
            assert registry.wait_for_state("srv-restart-halt", "running", timeout=15.0)

            runner = registry.runner_for("srv-restart-halt")
            assert isinstance(runner, ProcessServerRunner)
            supervisor = runner.supervisor

            # Crash the worker to trigger restart recovery
            with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_process_supervisor"):
                runner.send_debug_opcode("DEBUG_ABORT")

                # While worker is in backoff, simulate capacity loss so restart is refused
                supervisor.resource_limits.max_process_workers = 0
                supervisor.resource_limits.max_total_rss_mb = 1.0

                # Wait for supervisor to halt restart cycle and mark failed
                assert registry.wait_for_state("srv-restart-halt", "failed", timeout=10.0)
                wait_until(
                    lambda: not supervisor.is_restarting("srv-restart-halt"),
                    timeout=5.0,
                    description="restart cycle stopped",
                )
                wait_until(
                    lambda: any(
                        "mcp_worker_restart_admission_rejected" in r.message
                        and r.levelno == logging.ERROR
                        for r in caplog.records
                    ),
                    timeout=5.0,
                    description="restart admission rejection error log",
                )

            # Assert retry stopped and did not loop through all max_retries
            assert not supervisor.is_restarting("srv-restart-halt")
            assert supervisor.state("srv-restart-halt") == "failed"
        finally:
            registry.stop_all()
