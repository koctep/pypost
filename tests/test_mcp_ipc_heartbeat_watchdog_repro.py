"""Red acceptance tests for isolated MCP worker active HEARTBEAT watchdog (PYPOST-1468).

Architecture: ai-tasks/PYPOST-1468/20-architecture.md § Mandatory — Failing Repro

Covers:
1. test_heartbeat_policy_validation_and_defaults
2. test_normal_worker_heartbeats_roundtrip_successfully
3. test_hung_worker_times_out_and_is_terminated_to_failed
4. test_disabled_watchdog_does_not_terminate_hung_worker
5. test_heartbeat_timeout_interplay_with_auto_restart
6. test_heartbeat_pong_mismatch_warning_logged
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

import pypost.models.settings as settings_mod
from pypost.core.mcp_process_supervisor import McpProcessSupervisor
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.mcp_server_runner import ProcessServerRunner
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import AppSettings, McpServerConfiguration
from tests.helpers.port_allocation import reserve_ephemeral_ports

pytestmark = pytest.mark.timeout(60)

_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


def _require_heartbeat_policy_cls() -> Any:
    """Return McpHeartbeatPolicy from pypost.models.settings or fail red."""
    policy_cls = getattr(settings_mod, "McpHeartbeatPolicy", None)
    assert policy_cls is not None, (
        "McpHeartbeatPolicy is not defined in pypost.models.settings"
    )
    return policy_cls


def _require_restart_policy_cls() -> Any:
    """Return McpWorkerRestartPolicy from pypost.models.settings or fail red."""
    policy_cls = getattr(settings_mod, "McpWorkerRestartPolicy", None)
    assert policy_cls is not None, (
        "McpWorkerRestartPolicy is not defined in pypost.models.settings"
    )
    return policy_cls


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


def _worker_pid(runner: ProcessServerRunner) -> int | None:
    """Return the current child process PID for a ProcessServerRunner."""
    supervisor = getattr(runner, "supervisor", None)
    if supervisor is None:
        return None
    record = supervisor._workers.get(runner.worker_id)
    if record is None or record.process is None:
        return None
    return record.process.pid


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
def test_heartbeat_policy_validation_and_defaults() -> None:
    """Validate McpHeartbeatPolicy defaults, bounds constraints, and host wiring."""
    policy_cls = _require_heartbeat_policy_cls()

    # 1. Defaults verification
    default_policy = policy_cls()
    assert default_policy.enabled is True
    assert default_policy.interval_s == pytest.approx(2.0)
    assert default_policy.timeout_s == pytest.approx(5.0)

    # 2. Custom valid parameters
    custom_policy = policy_cls(
        enabled=False,
        interval_s=0.5,
        timeout_s=1.5,
    )
    assert custom_policy.enabled is False
    assert custom_policy.interval_s == pytest.approx(0.5)
    assert custom_policy.timeout_s == pytest.approx(1.5)

    # 3. Invalidation: interval_s <= 0
    with pytest.raises(ValidationError):
        policy_cls(interval_s=0.0)
    with pytest.raises(ValidationError):
        policy_cls(interval_s=-1.0)

    # 4. Invalidation: timeout_s <= 0
    with pytest.raises(ValidationError):
        policy_cls(timeout_s=0.0)
    with pytest.raises(ValidationError):
        policy_cls(timeout_s=-0.5)

    # 5. Invalidation: timeout_s < interval_s
    with pytest.raises(ValidationError):
        policy_cls(interval_s=2.0, timeout_s=1.0)

    # 6. AppSettings wiring
    default_settings = AppSettings()
    assert hasattr(default_settings, "mcp_heartbeat_policy")
    assert isinstance(default_settings.mcp_heartbeat_policy, policy_cls)
    assert default_settings.mcp_heartbeat_policy.enabled is True

    custom_settings = AppSettings(mcp_heartbeat_policy=custom_policy)
    assert custom_settings.mcp_heartbeat_policy == custom_policy

    # 7. McpProcessSupervisor wiring
    supervisor = McpProcessSupervisor(heartbeat_policy=custom_policy)
    try:
        assert hasattr(supervisor, "heartbeat_policy")
        assert supervisor.heartbeat_policy == custom_policy
    finally:
        supervisor.shutdown()

    # 8. MCPServerRegistry wiring
    registry = MCPServerRegistry(
        execution_mode="process",
        heartbeat_policy=custom_policy,
    )
    try:
        assert hasattr(registry, "heartbeat_policy")
        assert registry.heartbeat_policy == custom_policy
        assert registry._process_supervisor is not None
        assert registry._process_supervisor.heartbeat_policy == custom_policy
    finally:
        registry.stop_all()

    # Thread mode preserves execution mode isolation (no supervisor instantiated)
    thread_reg = MCPServerRegistry(heartbeat_policy=custom_policy)
    try:
        assert thread_reg._process_supervisor is None
    finally:
        thread_reg.stop_all()


@pytest.mark.timeout(30)
def test_normal_worker_heartbeats_roundtrip_successfully(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Normal worker replies to supervisor HEARTBEAT with HEARTBEAT_PONG."""
    policy_cls = _require_heartbeat_policy_cls()
    policy = policy_cls(
        enabled=True,
        interval_s=0.2,
        timeout_s=0.6,
    )
    col, env = _make_dummy_collection_and_env("hb-roundtrip")

    with reserve_ephemeral_ports(1) as (port,):
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            heartbeat_policy=policy,
        )
        try:
            with caplog.at_level(
                logging.DEBUG, logger="pypost.core.mcp_process_supervisor"
            ):
                registry.upsert(
                    McpServerConfiguration(
                        id="srv-hb-normal",
                        host="127.0.0.1",
                        port=port,
                        collection_id=col.id,
                        environment_id=env.id,
                        enabled=True,
                    )
                )
                registry.start("srv-hb-normal")
                assert registry.wait_for_state(
                    "srv-hb-normal", "running", timeout=15.0
                )
                runner = registry.runner_for("srv-hb-normal")
                assert isinstance(runner, ProcessServerRunner)
                assert runner.is_running()

                supervisor = registry._process_supervisor
                assert supervisor is not None

                # Allow multiple heartbeat intervals to elapse
                time.sleep(0.6)

                # Confirm worker remains running and supervisor recorded pong receipt
                assert registry.status("srv-hb-normal").state == "running"
                assert runner.is_running()

                record = supervisor._workers["srv-hb-normal"]
                assert getattr(record, "last_heartbeat_pong_at", 0.0) > 0.0
                assert getattr(record, "pending_heartbeat_nonce", None) is None

                # Verify supervisor emitted structured mcp_worker_heartbeat_pong log
                assert any(
                    "mcp_worker_heartbeat_pong" in r.message
                    and "instance_id=srv-hb-normal" in r.message
                    and "latency_s=" in r.message
                    and r.levelno == logging.DEBUG
                    for r in caplog.records
                )
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_hung_worker_times_out_and_is_terminated_to_failed(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Hung worker failing to pong within timeout is terminated to failed state."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    policy_cls = _require_heartbeat_policy_cls()
    policy = policy_cls(
        enabled=True,
        interval_s=0.2,
        timeout_s=0.4,
    )
    col, env = _make_dummy_collection_and_env("hb-hung")

    with reserve_ephemeral_ports(1) as (port,):
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            heartbeat_policy=policy,
        )
        try:
            registry.upsert(
                McpServerConfiguration(
                    id="srv-hb-hung",
                    host="127.0.0.1",
                    port=port,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )
            with caplog.at_level(logging.ERROR, logger="pypost.core.mcp_process_supervisor"):
                registry.start("srv-hb-hung")
                assert registry.wait_for_state("srv-hb-hung", "running", timeout=15.0)
                runner = registry.runner_for("srv-hb-hung")
                assert isinstance(runner, ProcessServerRunner)
                pid = _worker_pid(runner)
                assert pid is not None

                runner.send_debug_opcode("DEBUG_HANG")

                # Watchdog must detect timeout within bounded window and mark worker failed
                assert registry.wait_for_state("srv-hb-hung", "failed", timeout=5.0)
                assert not runner.is_running()
                assert runner.worker_is_alive() is False

                # Verify supervisor emitted mcp_worker_heartbeat_timeout log
                wait_until(
                    lambda: any(
                        "mcp_worker_heartbeat_timeout" in r.message
                        and "instance_id=srv-hb-hung" in r.message
                        and f"pid={pid}" in r.message
                        and "timeout_s=0.40" in r.message
                        and r.levelno == logging.ERROR
                        for r in caplog.records
                    ),
                    timeout=5.0,
                    description="mcp_worker_heartbeat_timeout log entry",
                )
                status = registry.status("srv-hb-hung")
                assert "heartbeat" in status.message.lower()
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_disabled_watchdog_does_not_terminate_hung_worker(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Disabled watchdog policy does not probe or terminate a frozen worker."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    policy_cls = _require_heartbeat_policy_cls()
    policy = policy_cls(
        enabled=False,
        interval_s=0.2,
        timeout_s=0.4,
    )
    col, env = _make_dummy_collection_and_env("hb-disabled")

    with reserve_ephemeral_ports(1) as (port,):
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            heartbeat_policy=policy,
        )
        try:
            registry.upsert(
                McpServerConfiguration(
                    id="srv-hb-disabled",
                    host="127.0.0.1",
                    port=port,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )
            with caplog.at_level(logging.ERROR, logger="pypost.core.mcp_process_supervisor"):
                registry.start("srv-hb-disabled")
                assert registry.wait_for_state("srv-hb-disabled", "running", timeout=15.0)
                runner = registry.runner_for("srv-hb-disabled")
                assert isinstance(runner, ProcessServerRunner)
                assert runner.is_running()

                runner.send_debug_opcode("DEBUG_HANG")

                # Wait well beyond normal timeout duration (0.8s > 0.4s)
                time.sleep(0.8)

                # Worker must still be alive and reported running by registry
                assert runner.worker_is_alive() is True
                assert registry.status("srv-hb-disabled").state == "running"
                assert not any(
                    "mcp_worker_heartbeat_timeout" in r.message for r in caplog.records
                )
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_heartbeat_timeout_interplay_with_auto_restart(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Heartbeat timeout triggers termination and auto-restart when restart policy is enabled."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    heartbeat_policy_cls = _require_heartbeat_policy_cls()
    restart_policy_cls = _require_restart_policy_cls()

    hb_policy = heartbeat_policy_cls(
        enabled=True,
        interval_s=0.2,
        timeout_s=0.4,
    )
    rst_policy = restart_policy_cls(
        enabled=True,
        max_retries=2,
        initial_backoff_s=0.1,
        max_backoff_s=0.5,
    )
    col, env = _make_dummy_collection_and_env("hb-restart")

    with reserve_ephemeral_ports(1) as (port,):
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: col if cid == col.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            heartbeat_policy=hb_policy,
            restart_policy=rst_policy,
        )
        try:
            registry.upsert(
                McpServerConfiguration(
                    id="srv-hb-restart",
                    host="127.0.0.1",
                    port=port,
                    collection_id=col.id,
                    environment_id=env.id,
                    enabled=True,
                )
            )
            with caplog.at_level(logging.ERROR, logger="pypost.core.mcp_process_supervisor"):
                registry.start("srv-hb-restart")
                assert registry.wait_for_state("srv-hb-restart", "running", timeout=15.0)
                runner = registry.runner_for("srv-hb-restart")
                assert isinstance(runner, ProcessServerRunner)
                initial_pid = _worker_pid(runner)
                assert initial_pid is not None

                runner.send_debug_opcode("DEBUG_HANG")

                # Heartbeat timeout triggers termination followed by auto-restart backoff
                wait_until(
                    lambda: any(
                        "mcp_worker_heartbeat_timeout" in r.message
                        and "instance_id=srv-hb-restart" in r.message
                        and f"pid={initial_pid}" in r.message
                        and "timeout_s=0.40" in r.message
                        and r.levelno == logging.ERROR
                        for r in caplog.records
                    ),
                    timeout=5.0,
                    description="heartbeat timeout detection before auto-restart",
                )

                # Supervisor should respawn a new worker process
                wait_until(
                    lambda: (
                        _worker_pid(runner) is not None
                        and _worker_pid(runner) != initial_pid
                    ),
                    timeout=10.0,
                    description="worker respawn with new PID",
                )
                assert registry.wait_for_state("srv-hb-restart", "running", timeout=15.0)
                assert runner.is_running()
                assert runner.worker_is_alive() is True
        finally:
            registry.stop_all()


@pytest.mark.timeout(10)
def test_heartbeat_pong_mismatch_warning_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Mismatched or unsolicited HEARTBEAT_PONG logs a warning."""
    from pypost.core.mcp_process_supervisor import _WorkerRecord
    from pypost.core.mcp_worker_ipc import make_message

    policy_cls = _require_heartbeat_policy_cls()
    supervisor = McpProcessSupervisor(heartbeat_policy=policy_cls())
    try:
        with caplog.at_level(
            logging.WARNING, logger="pypost.core.mcp_process_supervisor"
        ):
            record = _WorkerRecord(
                instance_id="srv-mismatch-test",
                process=None,
                parent_conn=None,
                pending_heartbeat_nonce="nonce-expected",
            )
            with supervisor._lock:
                supervisor._workers["srv-mismatch-test"] = record

            supervisor._apply_ipc_message(
                "srv-mismatch-test",
                make_message("HEARTBEAT_PONG", nonce="nonce-unexpected"),
            )

            assert any(
                "mcp_worker_heartbeat_pong_mismatch" in r.message
                and "srv-mismatch-test" in r.message
                and "expected=nonce-expected" in r.message
                and "got=nonce-unexpected" in r.message
                and r.levelno == logging.WARNING
                for r in caplog.records
            )
    finally:
        supervisor.shutdown()
