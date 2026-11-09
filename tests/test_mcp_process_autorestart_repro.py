"""Red acceptance tests for isolated MCP worker auto-restart policy (PYPOST-1466).

Architecture: ai-tasks/PYPOST-1466/20-architecture.md § Mandatory — Failing Repro

Covers:
1. McpWorkerRestartPolicy defaults, validation bounds, and host wiring
2. Default disabled policy (enabled=False) immediate failure without retry (FR1)
3. Opt-in exponential backoff recovery preserving refreshed tools/variables/secrets (FR2, FR5)
4. Bounded retry exhaustion transitioning to terminal failed state (FR2, FR3, NFR1)
5. Healthy stability window resetting consecutive retry counter (FR4)
6. Immediate cancellation of pending backoff on stop and stop_all (FR6, NFR2)
7. Initial startup failure failing immediately without entering auto-restart loop (FR7)
"""

from __future__ import annotations

import json
import logging
import socket
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator
from unittest.mock import MagicMock

import anyio
import pytest
from pydantic import ValidationError
from PySide6.QtCore import QCoreApplication, QObject, Signal

import pypost.models.settings as settings_mod
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.mcp_server_runner import ProcessServerRunner
from pypost.core.qt.daemon_runtime import DaemonRuntime
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.mcp_server_controller import McpServerSettingsController
from tests.helpers.mcp_live_server import wait_for_port
from tests.helpers.port_allocation import reserve_ephemeral_ports
from tests.test_mcp_server_integration import _mcp_call_tool, _mcp_list_tools

pytestmark = pytest.mark.timeout(60)

_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


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
    """Poll ``predicate`` until it returns True or ``timeout`` expires."""
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
    record = runner.supervisor._workers.get(runner.worker_id)
    if record is None or record.process is None:
        return None
    return record.process.pid


@contextmanager
def _local_echo_http_server() -> Iterator[tuple[int, list[dict[str, Any]]]]:
    """Run a bounded local HTTP stub server that echoes request metadata as JSON."""
    recorded: list[dict[str, Any]] = []
    lock = threading.Lock()

    class _EchoHandler(BaseHTTPRequestHandler):
        def _handle(self) -> None:
            headers = {k.lower(): v for k, v in self.headers.items()}
            entry = {
                "method": self.command,
                "path": self.path,
                "headers": headers,
            }
            with lock:
                recorded.append(entry)
            payload = json.dumps(entry).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_GET = _handle
        do_POST = _handle

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
    port = int(httpd.server_address[1])
    thread = threading.Thread(
        target=httpd.serve_forever,
        name=f"autorestart-echo-http-{port}",
        daemon=True,
    )
    thread.start()
    try:
        yield port, recorded
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2.0)


class _FakeDaemonMetrics(QObject):
    listening_changed = Signal(bool)
    unexpected_exit = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.is_listening = False
        self.stopped = False

    def connect_start_failed(self, _slot: Any) -> None:
        return None

    def start_server(self, _host: str, _port: int) -> None:
        self.is_listening = True
        self.listening_changed.emit(True)

    def stop_server(self) -> None:
        self.stopped = True


class _EmptyDaemonStorage:
    def apply_encryption_settings(self, _settings: Any) -> None:
        return None

    def load_collections_snapshot_strict(self, *, required_ids: set[str]) -> dict[str, Any]:
        assert not required_ids
        return {}

    def load_environments_snapshot_strict(self, *, required_ids: set[str]) -> dict[str, Any]:
        assert not required_ids
        return {}


@pytest.mark.timeout(20)
def test_restart_policy_settings_defaults_and_validation(tmp_path: Path) -> None:
    """AppSettings.mcp_restart_policy defaults, validates bounds, and wires to hosts."""
    policy_cls = _require_restart_policy_cls()

    default_settings = AppSettings()
    default_policy = getattr(default_settings, "mcp_restart_policy", None)
    assert isinstance(default_policy, policy_cls)
    assert default_policy.enabled is False
    assert default_policy.max_retries == 3
    assert default_policy.initial_backoff_s == pytest.approx(0.5)
    assert default_policy.max_backoff_s == pytest.approx(8.0)
    assert default_policy.backoff_multiplier == pytest.approx(2.0)
    assert default_policy.healthy_reset_window_s == pytest.approx(30.0)

    assert default_policy.backoff_for_attempt(1) == pytest.approx(0.5)
    assert default_policy.backoff_for_attempt(2) == pytest.approx(1.0)
    assert default_policy.backoff_for_attempt(3) == pytest.approx(2.0)
    assert default_policy.backoff_for_attempt(6) == pytest.approx(8.0)

    custom_policy = policy_cls(
        enabled=True,
        max_retries=4,
        initial_backoff_s=0.2,
        max_backoff_s=1.6,
        backoff_multiplier=2.0,
        healthy_reset_window_s=15.0,
    )
    custom_settings = AppSettings(
        mcp_execution_mode="process",
        mcp_restart_policy=custom_policy,
    )
    assert custom_settings.mcp_restart_policy == custom_policy

    with pytest.raises(ValidationError):
        policy_cls(max_retries=-1)
    with pytest.raises(ValidationError):
        policy_cls(max_retries=101)
    with pytest.raises(ValidationError):
        policy_cls(initial_backoff_s=0.0)
    with pytest.raises(ValidationError):
        policy_cls(initial_backoff_s=0.5, max_backoff_s=0.2)
    with pytest.raises(ValidationError):
        policy_cls(backoff_multiplier=0.5)
    with pytest.raises(ValidationError):
        policy_cls(healthy_reset_window_s=-1.0)

    controller = McpServerSettingsController(
        settings_provider=lambda: custom_settings,
        collection_lookup=lambda _id: None,
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
    )
    try:
        assert controller.registry._process_supervisor is not None
        assert controller.registry._process_supervisor.restart_policy == custom_policy
    finally:
        controller.registry.stop_all()
        if controller.registry._process_supervisor is not None:
            controller.registry._process_supervisor.shutdown()

    QCoreApplication.instance() or QCoreApplication([])
    runtime = DaemonRuntime(
        SimpleNamespace(
            collections_dir=tmp_path,
            environments_dir=tmp_path,
            collections_source="cli",
            environments_source="cli",
        ),
        config_manager=SimpleNamespace(load_config_strict=lambda: custom_settings),
        storage=_EmptyDaemonStorage(),
        metrics=_FakeDaemonMetrics(),
    )
    runtime.start()
    try:
        assert runtime.is_ready
        assert runtime._registry is not None
        assert runtime._registry._process_supervisor is not None
        assert runtime._registry._process_supervisor.restart_policy == custom_policy
    finally:
        runtime.shutdown()


@pytest.mark.timeout(60)
def test_default_policy_disabled_fails_immediately_without_retry(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Default restart policy (enabled=False) transitions crashed worker to failed immediately."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")

    with reserve_ephemeral_ports(2) as ports:
        crash_port, peer_port = ports[0], ports[1]
        peer_url = f"http://127.0.0.1:{peer_port}/mcp"

        collection = Collection(
            id="col-default-disabled",
            requests=[
                RequestData(
                    id="req-default",
                    name="default_tool",
                    method="GET",
                    url="http://127.0.0.1/default",
                    expose_as_mcp=True,
                )
            ],
        )
        env = Environment(id="env-default-disabled", variables={})
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: collection if cid == collection.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
        )
        try:
            for srv_id, port in (("srv-crash", crash_port), ("srv-peer", peer_port)):
                registry.upsert(
                    McpServerConfiguration(
                        id=srv_id,
                        host="127.0.0.1",
                        port=port,
                        collection_id=collection.id,
                        environment_id=env.id,
                        enabled=True,
                    )
                )
                ports.release()
                registry.start(srv_id)
                assert registry.wait_for_state(srv_id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", port, timeout=15.0)

            runner = registry.runner_for("srv-crash")
            assert isinstance(runner, ProcessServerRunner)

            with caplog.at_level(
                logging.ERROR, logger="pypost.core.mcp_server_registry"
            ):
                runner.send_debug_opcode("DEBUG_ABORT")
                assert registry.wait_for_state("srv-crash", "failed", timeout=5.0)

            assert registry.status("srv-peer").state == "running"
            assert anyio.run(_mcp_list_tools, peer_url) == ["default_tool"]

            policy_cls = _require_restart_policy_cls()
            assert isinstance(AppSettings().mcp_restart_policy, policy_cls)
            assert AppSettings().mcp_restart_policy.enabled is False
            assert runner.supervisor.restart_policy.enabled is False
            assert runner.supervisor.retry_count(runner.worker_id) == 0
            assert runner.supervisor.is_restarting(runner.worker_id) is False
        finally:
            registry.stop_all()


@pytest.mark.timeout(60)
def test_auto_restart_recovers_crashed_worker_with_exponential_backoff_and_latest_state(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Enabled policy restarts a crashed worker with backoff and preserves refreshed state."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    policy_cls = _require_restart_policy_cls()
    policy = policy_cls(
        enabled=True,
        max_retries=3,
        initial_backoff_s=0.1,
        max_backoff_s=0.4,
        backoff_multiplier=2.0,
        healthy_reset_window_s=10.0,
    )

    with _local_echo_http_server() as (stub_port, recorded):
        with reserve_ephemeral_ports(1) as ports:
            mcp_port = ports[0]
            mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"

            collection = Collection(
                id="col-autorestart-state",
                name="AutoRestart State Collection",
                variables=[
                    CollectionVariable(
                        name="col_stage",
                        type="string",
                        default="stage-v1",
                        required=True,
                        secret=False,
                    ),
                ],
                requests=[
                    RequestData(
                        id="req-alpha",
                        name="Get Alpha",
                        method="GET",
                        url=(
                            f"http://127.0.0.1:{stub_port}"
                            "/{{ col_stage }}/{{ env_region }}"
                        ),
                        headers={"X-Secret-Token": "{{ secret_token }}"},
                        expose_as_mcp=True,
                    )
                ],
            )
            environment = Environment(
                id="env-autorestart-state",
                name="AutoRestart Env",
                variables={
                    "env_region": "us-east-1",
                    "secret_token": "super-secret-token-v1",
                },
                hidden_keys={"secret_token"},
            )
            collections = {collection.id: collection}
            environments = {environment.id: environment}

            registry = MCPServerRegistry(
                collection_lookup=collections.get,
                environment_lookup=environments.get,
                execution_mode="process",
                restart_policy=policy,
            )
            config = McpServerConfiguration(
                id="srv-autorestart",
                host="127.0.0.1",
                port=mcp_port,
                collection_id=collection.id,
                environment_id=environment.id,
                enabled=True,
            )
            try:
                registry.upsert(config)
                ports.release()
                registry.start(config.id)
                assert registry.wait_for_state(config.id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", mcp_port, timeout=15.0)

                runner = registry.runner_for(config.id)
                assert isinstance(runner, ProcessServerRunner)
                initial_pid = _worker_pid(runner)
                assert initial_pid is not None

                # Refresh collection tools and environment variables before the crash.
                collection.variables = [
                    CollectionVariable(
                        name="col_stage",
                        type="string",
                        default="stage-v2-refreshed",
                        required=True,
                        secret=False,
                    ),
                ]
                collection.requests = [
                    RequestData(
                        id="req-alpha",
                        name="Get Alpha",
                        method="GET",
                        url=(
                            f"http://127.0.0.1:{stub_port}"
                            "/{{ col_stage }}/{{ env_region }}"
                        ),
                        headers={"X-Secret-Token": "{{ secret_token }}"},
                        expose_as_mcp=True,
                    ),
                    RequestData(
                        id="req-recovered",
                        name="Get Recovered",
                        method="GET",
                        url=(
                            f"http://127.0.0.1:{stub_port}"
                            "/recovered/{{ col_stage }}/{{ env_region }}"
                        ),
                        headers={"X-Secret-Token": "{{ secret_token }}"},
                        expose_as_mcp=True,
                    ),
                ]
                registry.refresh_collection(collection.id)

                environment.variables = {
                    "env_region": "eu-central-1",
                    "secret_token": "super-secret-token-v2-rotated",
                }
                registry.refresh_environment(environment.id)

                wait_until(
                    lambda: sorted(anyio.run(_mcp_list_tools, mcp_url))
                    == ["get_alpha", "get_recovered"],
                    timeout=3.0,
                    description="pre-crash tool refresh",
                )

                with caplog.at_level(
                    logging.INFO, logger="pypost.core.mcp_process_supervisor"
                ):
                    runner.send_debug_opcode("DEBUG_ABORT")
                    wait_until(
                        lambda: (
                            _worker_pid(runner) not in (None, initial_pid)
                            and runner.is_running()
                            and registry.status(config.id).state == "running"
                        ),
                        timeout=10.0,
                        description="worker auto-restart recovery with new PID",
                    )

                recovered_pid = _worker_pid(runner)
                assert recovered_pid is not None
                assert recovered_pid != initial_pid
                assert runner.supervisor.retry_count(runner.worker_id) == 1
                assert runner.supervisor.is_restarting(runner.worker_id) is False

                wait_for_port("127.0.0.1", mcp_port, timeout=10.0)
                wait_until(
                    lambda: sorted(anyio.run(_mcp_list_tools, mcp_url))
                    == ["get_alpha", "get_recovered"],
                    timeout=5.0,
                    description="post-restart tools availability",
                )

                res = anyio.run(_mcp_call_tool, mcp_url, "get_recovered", {})
                assert "/recovered/stage-v2-refreshed/eu-central-1" in res["body"]
                assert "super-secret-token-v2-rotated" not in res["body"]
                assert any(
                    entry["headers"].get("x-secret-token")
                    == "super-secret-token-v2-rotated"
                    for entry in recorded
                )

                scheduled_msgs = [
                    rec.message
                    for rec in caplog.records
                    if "mcp_worker_restart_scheduled" in rec.message
                ]
                assert len(scheduled_msgs) == 1
                assert f"instance_id={config.id}" in scheduled_msgs[0]
                assert "attempt=1" in scheduled_msgs[0]
                assert f"max_retries={policy.max_retries}" in scheduled_msgs[0]
                assert "delay_s=0.10" in scheduled_msgs[0]
                assert "exitcode=" in scheduled_msgs[0]

                restarted_msgs = [
                    rec.message
                    for rec in caplog.records
                    if "mcp_worker_restarted" in rec.message
                ]
                assert len(restarted_msgs) == 1
                assert f"instance_id={config.id}" in restarted_msgs[0]
                assert f"pid={recovered_pid}" in restarted_msgs[0]
                assert "attempt=1" in restarted_msgs[0]
                assert f"max_retries={policy.max_retries}" in restarted_msgs[0]

                # FR8: Verify secret values, variables, headers, and tool payloads are never logged.
                assert "super-secret-token-v1" not in caplog.text
                assert "super-secret-token-v2-rotated" not in caplog.text
                assert f"http://127.0.0.1:{stub_port}" not in caplog.text
                assert "X-Secret-Token" not in caplog.text
                assert "col_stage" not in caplog.text
                assert "env_region" not in caplog.text
            finally:
                registry.stop_all()


@pytest.mark.timeout(60)
def test_auto_restart_exhaustion_transitions_to_failed_after_max_retries(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Repeated crashes exhaust max_retries with progressive backoff and enter failed state."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    policy_cls = _require_restart_policy_cls()
    policy = policy_cls(
        enabled=True,
        max_retries=2,
        initial_backoff_s=0.08,
        max_backoff_s=0.5,
        backoff_multiplier=2.0,
        healthy_reset_window_s=30.0,
    )

    with reserve_ephemeral_ports(1) as ports:
        mcp_port = ports[0]
        collection = Collection(
            id="col-exhaust",
            requests=[
                RequestData(
                    id="req-exhaust",
                    name="exhaust_tool",
                    method="GET",
                    url="http://127.0.0.1/exhaust",
                    expose_as_mcp=True,
                )
            ],
        )
        env = Environment(id="env-exhaust", variables={})
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: collection if cid == collection.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            restart_policy=policy,
        )
        config = McpServerConfiguration(
            id="srv-exhaust",
            host="127.0.0.1",
            port=mcp_port,
            collection_id=collection.id,
            environment_id=env.id,
            enabled=True,
        )
        try:
            registry.upsert(config)
            ports.release()
            registry.start(config.id)
            assert registry.wait_for_state(config.id, "running", timeout=15.0)
            wait_for_port("127.0.0.1", mcp_port, timeout=15.0)

            runner = registry.runner_for(config.id)
            assert isinstance(runner, ProcessServerRunner)
            pid_0 = _worker_pid(runner)
            assert pid_0 is not None

            with caplog.at_level(
                logging.INFO, logger="pypost.core.mcp_process_supervisor"
            ):
                # Crash 1 -> Retry 1 (delay ~0.08s)
                runner.send_debug_opcode("DEBUG_ABORT")
                wait_until(
                    lambda: (
                        _worker_pid(runner) not in (None, pid_0)
                        and runner.is_running()
                    ),
                    timeout=10.0,
                    description="retry 1 recovery",
                )
                pid_1 = _worker_pid(runner)
                assert pid_1 is not None
                assert runner.supervisor.retry_count(runner.worker_id) == 1

                # Crash 2 -> Retry 2 (delay ~0.16s)
                runner.send_debug_opcode("DEBUG_ABORT")
                wait_until(
                    lambda: (
                        _worker_pid(runner) not in (None, pid_0, pid_1)
                        and runner.is_running()
                    ),
                    timeout=10.0,
                    description="retry 2 recovery",
                )
                assert runner.supervisor.retry_count(runner.worker_id) == 2

                # Crash 3 -> Exhausted (max_retries=2), transitions to terminal failed
                runner.send_debug_opcode("DEBUG_ABORT")
                assert registry.wait_for_state(config.id, "failed", timeout=5.0)

            assert runner.supervisor.is_restarting(runner.worker_id) is False
            time.sleep(0.25)
            assert registry.status(config.id).state == "failed"
            assert runner.worker_is_alive() is False

            scheduled_msgs = [
                rec.message
                for rec in caplog.records
                if "mcp_worker_restart_scheduled" in rec.message
            ]
            assert len(scheduled_msgs) == 2
            assert "delay_s=0.08" in scheduled_msgs[0]
            assert "delay_s=0.16" in scheduled_msgs[1]
            exhausted_msgs = [
                rec.message
                for rec in caplog.records
                if "mcp_worker_restart_exhausted" in rec.message
            ]
            assert len(exhausted_msgs) == 1
            assert f"instance_id={config.id}" in exhausted_msgs[0]
            assert "attempts=2" in exhausted_msgs[0]
            assert f"max_retries={policy.max_retries}" in exhausted_msgs[0]
            assert "exitcode=" in exhausted_msgs[0]
        finally:
            registry.stop_all()


@pytest.mark.timeout(60)
def test_healthy_reset_window_resets_retry_counter_for_later_crash(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Sustained healthy uptime >= healthy_reset_window_s resets retry_count to 0."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    policy_cls = _require_restart_policy_cls()
    policy = policy_cls(
        enabled=True,
        max_retries=1,
        initial_backoff_s=0.05,
        max_backoff_s=0.2,
        backoff_multiplier=2.0,
        healthy_reset_window_s=0.25,
    )

    with reserve_ephemeral_ports(1) as ports:
        mcp_port = ports[0]
        mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"
        collection = Collection(
            id="col-reset-window",
            requests=[
                RequestData(
                    id="req-reset",
                    name="reset_window_tool",
                    method="GET",
                    url="http://127.0.0.1/reset",
                    expose_as_mcp=True,
                )
            ],
        )
        env = Environment(id="env-reset-window", variables={})
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: collection if cid == collection.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            restart_policy=policy,
        )
        config = McpServerConfiguration(
            id="srv-reset-window",
            host="127.0.0.1",
            port=mcp_port,
            collection_id=collection.id,
            environment_id=env.id,
            enabled=True,
        )
        try:
            registry.upsert(config)
            ports.release()
            registry.start(config.id)
            assert registry.wait_for_state(config.id, "running", timeout=15.0)
            wait_for_port("127.0.0.1", mcp_port, timeout=15.0)

            runner = registry.runner_for(config.id)
            assert isinstance(runner, ProcessServerRunner)
            pid_0 = _worker_pid(runner)
            assert pid_0 is not None

            with caplog.at_level(
                logging.INFO, logger="pypost.core.mcp_process_supervisor"
            ):
                # First crash consumes the single retry budget (1/1).
                runner.send_debug_opcode("DEBUG_ABORT")
                wait_until(
                    lambda: (
                        _worker_pid(runner) not in (None, pid_0)
                        and runner.is_running()
                        and registry.status(config.id).state == "running"
                    ),
                    timeout=10.0,
                    description="first crash recovery",
                )
                pid_1 = _worker_pid(runner)
                assert pid_1 is not None

                # Wait for healthy_reset_window_s (0.25s) to reset retry_count to 0.
                wait_until(
                    lambda: runner.supervisor.retry_count(runner.worker_id) == 0,
                    timeout=3.0,
                    description="retry counter reset after healthy uptime window",
                )

                # Second transient crash after reset must also recover with a new PID.
                runner.send_debug_opcode("DEBUG_ABORT")
                wait_until(
                    lambda: (
                        _worker_pid(runner) not in (None, pid_0, pid_1)
                        and runner.is_running()
                        and registry.status(config.id).state == "running"
                    ),
                    timeout=10.0,
                    description="second crash recovery after counter reset",
                )

            wait_for_port("127.0.0.1", mcp_port, timeout=10.0)
            wait_until(
                lambda: anyio.run(_mcp_list_tools, mcp_url) == ["reset_window_tool"],
                timeout=5.0,
                description="recovered server tool listing",
            )
            reset_msgs = [
                rec.message
                for rec in caplog.records
                if "mcp_worker_restart_counter_reset" in rec.message
            ]
            assert len(reset_msgs) == 1
            assert f"instance_id={config.id}" in reset_msgs[0]
            assert f"pid={pid_1}" in reset_msgs[0]
            assert "uptime_s=" in reset_msgs[0]
            assert "previous_retry_count=1" in reset_msgs[0]
        finally:
            registry.stop_all()


@pytest.mark.timeout(60)
def test_operator_stop_and_shutdown_cancel_pending_backoff_immediately(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Explicit stop(id) and stop_all() cancel long backoff waits in <1.0s without respawn."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    policy_cls = _require_restart_policy_cls()
    policy = policy_cls(
        enabled=True,
        max_retries=3,
        initial_backoff_s=5.0,
        max_backoff_s=10.0,
        backoff_multiplier=2.0,
        healthy_reset_window_s=30.0,
    )

    with reserve_ephemeral_ports(2) as ports:
        stop_port, shutdown_port = ports[0], ports[1]
        collection = Collection(
            id="col-cancel-backoff",
            requests=[
                RequestData(
                    id="req-cancel",
                    name="cancel_tool",
                    method="GET",
                    url="http://127.0.0.1/cancel",
                    expose_as_mcp=True,
                )
            ],
        )
        env = Environment(id="env-cancel-backoff", variables={})
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: collection if cid == collection.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            restart_policy=policy,
        )
        try:
            for srv_id, port in (
                ("srv-stop", stop_port),
                ("srv-shutdown", shutdown_port),
            ):
                registry.upsert(
                    McpServerConfiguration(
                        id=srv_id,
                        host="127.0.0.1",
                        port=port,
                        collection_id=collection.id,
                        environment_id=env.id,
                        enabled=True,
                    )
                )
                ports.release()
                registry.start(srv_id)
                assert registry.wait_for_state(srv_id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", port, timeout=15.0)

            runner_stop = registry.runner_for("srv-stop")
            runner_shutdown = registry.runner_for("srv-shutdown")
            assert isinstance(runner_stop, ProcessServerRunner)
            assert isinstance(runner_shutdown, ProcessServerRunner)

            with caplog.at_level(
                logging.INFO, logger="pypost.core.mcp_process_supervisor"
            ):
                # 1. Crash srv-stop so it enters the 5.0s backoff wait, then stop(id).
                runner_stop.send_debug_opcode("DEBUG_ABORT")
                wait_until(
                    lambda: runner_stop.supervisor.is_restarting(runner_stop.worker_id),
                    timeout=3.0,
                    description="srv-stop entering backoff wait",
                )
                assert registry.status("srv-stop").state == "starting"

                t0 = time.monotonic()
                registry.stop("srv-stop")
                stop_elapsed = time.monotonic() - t0
                assert stop_elapsed < 1.0, f"stop() took {stop_elapsed:.3f}s >= 1.0s"
                assert registry.status("srv-stop").state == "stopped"
                assert runner_stop.supervisor.is_restarting(runner_stop.worker_id) is False
                assert runner_stop.worker_is_alive() is False

                # 2. Crash srv-shutdown so it enters the 5.0s backoff wait, then
                # supervisor shutdown.
                runner_shutdown.send_debug_opcode("DEBUG_ABORT")
                wait_until(
                    lambda: runner_shutdown.supervisor.is_restarting(
                        runner_shutdown.worker_id
                    ),
                    timeout=3.0,
                    description="srv-shutdown entering backoff wait",
                )

                t1 = time.monotonic()
                assert registry._process_supervisor is not None
                registry._process_supervisor.shutdown()
                registry.stop_all()
                shutdown_elapsed = time.monotonic() - t1
                assert shutdown_elapsed < 1.0, (
                    f"shutdown took {shutdown_elapsed:.3f}s >= 1.0s"
                )
                assert registry.status("srv-shutdown").state == "stopped"
                assert (
                    runner_shutdown.supervisor.is_restarting(runner_shutdown.worker_id)
                    is False
                )
                assert runner_shutdown.worker_is_alive() is False

            cancelled_msgs = [
                rec.message
                for rec in caplog.records
                if "mcp_worker_restart_cancelled" in rec.message
            ]
            assert any(
                "instance_id=srv-stop" in msg
                and "attempt=1" in msg
                and "reason=operator_stop" in msg
                for msg in cancelled_msgs
            )
            assert any(
                "instance_id=srv-shutdown" in msg
                and "attempt=1" in msg
                and "reason=supervisor_shutdown" in msg
                for msg in cancelled_msgs
            )
        finally:
            registry.stop_all()


@pytest.mark.timeout(30)
def test_initial_start_failure_does_not_trigger_auto_restart() -> None:
    """Initial operator-initiated startup failure fails immediately with zero retries."""
    policy_cls = _require_restart_policy_cls()
    policy = policy_cls(
        enabled=True,
        max_retries=3,
        initial_backoff_s=0.05,
        max_backoff_s=0.2,
        backoff_multiplier=2.0,
        healthy_reset_window_s=30.0,
    )

    with reserve_ephemeral_ports(1) as ports:
        occupied_port = ports[0]
        collection = Collection(
            id="col-init-fail",
            requests=[
                RequestData(
                    id="req-init-fail",
                    name="init_fail_tool",
                    method="GET",
                    url="http://127.0.0.1/init-fail",
                    expose_as_mcp=True,
                )
            ],
        )
        env = Environment(id="env-init-fail", variables={})
        registry = MCPServerRegistry(
            collection_lookup=lambda cid: collection if cid == collection.id else None,
            environment_lookup=lambda eid: env if eid == env.id else None,
            execution_mode="process",
            restart_policy=policy,
        )
        config = McpServerConfiguration(
            id="srv-init-fail",
            host="127.0.0.1",
            port=occupied_port,
            collection_id=collection.id,
            environment_id=env.id,
            enabled=True,
        )
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        blocker.bind(("127.0.0.1", occupied_port))
        blocker.listen(1)
        try:
            registry.upsert(config)
            ports.release()
            registry.start(config.id)
            assert registry.status(config.id).state == "failed"

            runner = registry.runner_for(config.id)
            assert isinstance(runner, ProcessServerRunner)
            assert runner.supervisor.is_restarting(runner.worker_id) is False
            assert runner.supervisor.retry_count(runner.worker_id) == 0
        finally:
            blocker.close()

        try:
            # Even after the port blocker closes and initial_backoff_s passes,
            # no background auto-restart should occur for an initial start failure.
            time.sleep(0.2)
            assert registry.status(config.id).state == "failed"
            assert runner.supervisor.is_restarting(runner.worker_id) is False
            assert runner.supervisor.retry_count(runner.worker_id) == 0
            assert runner.worker_is_alive() is False
        finally:
            registry.stop_all()
