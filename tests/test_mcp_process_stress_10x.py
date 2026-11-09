"""High-density 10x process-mode stress parity and Windows stop escalation tests.

Jira: PYPOST-1470
Architecture: ai-tasks/PYPOST-1470/20-architecture.md
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
from pathlib import Path
import socket
import struct
import sys
import threading
import time
from typing import Any

import anyio
import pytest

from pypost.core.mcp_process_supervisor import (
    DEFAULT_STOP_BUDGET_S,
    McpProcessSupervisor,
)
from pypost.core.mcp_server_runner import ProcessServerRunner
from pypost.models.settings import McpServerConfiguration
from tests.helpers.collection_integration_harness import (
    CollectionVariablesIntegrationHarness,
)
from tests.helpers.mcp_live_server import wait_for_port
from tests.helpers.port_allocation import (
    EphemeralPortReserve,
    reserve_ephemeral_ports,
)
from tests.test_mcp_server_integration import _mcp_call_tool, _mcp_list_tools

pytestmark = pytest.mark.timeout(120)

_STOP_BUDGET_S = DEFAULT_STOP_BUDGET_S + 1.0
_TEST_ECHO_VARS_ENV = "PYPOST_MCP_TEST_ECHO_VARS"
_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


def _make_collection(
    collection_id: str,
    tool_name: str,
    var_name: str | None = None,
    var_value: str = "",
) -> dict[str, Any]:
    variables = []
    if var_name:
        variables.append(
            {
                "name": var_name,
                "type": "string",
                "default": var_value,
                "required": True,
                "secret": False,
            }
        )
    return {
        "id": collection_id,
        "name": f"Collection {collection_id}",
        "variables": variables,
        "requests": [
            {
                "id": tool_name,
                "name": tool_name,
                "method": "GET",
                "url": f"http://127.0.0.1/{tool_name}",
                "expose_as_mcp": True,
            }
        ],
    }


def _upsert_standalone_process(
    harness: CollectionVariablesIntegrationHarness,
    *,
    index: int,
    port: int,
    prefix: str,
    tool_name: str,
    var_name: str | None = None,
    var_value: str = "",
) -> str:
    lib_id = f"lib-{prefix}-{index}"
    col_id = f"col-{prefix}-{index}"
    col_data = _make_collection(
        col_id,
        tool_name=tool_name,
        var_name=var_name,
        var_value=var_value,
    )
    harness.create_library(
        manifest_id=lib_id,
        is_legacy_manifest=False,
        collections_data={f"{col_id}.json": col_data},
    )
    server_id = f"standalone-{lib_id}-{col_id}"
    config = McpServerConfiguration.model_construct(
        id=server_id,
        name=f"Standalone {col_id}",
        host="127.0.0.1",
        port=port,
        server_type="local",
        library_id=lib_id,
        manifest_id=lib_id,
        library_collection_path=f"collections/{col_id}.json",
        library_collection_index=0,
        environment_id=None,
        enabled=True,
    )
    harness.registry.validate_library_candidate(config)
    harness.registry.upsert(config)
    return server_id


@pytest.mark.timeout(60)
def test_mcp_process_10x_parallel_startup_barrier_synchronization(
    tmp_path: Path,
) -> None:
    """10 process-mode servers launched concurrently using threading.Barrier(10),
    asserting all 10 reach running status, listening, and concurrent tools discovery.
    """
    with reserve_ephemeral_ports(10) as ports:
        with CollectionVariablesIntegrationHarness(
            tmp_path, execution_mode="process"
        ) as harness:
            server_configs: list[tuple[str, int]] = []
            for i, port in enumerate(ports, start=1):
                srv_id = _upsert_standalone_process(
                    harness,
                    index=i,
                    port=port,
                    prefix="pbar",
                    tool_name=f"tool_pbarrier_{i}",
                )
                server_configs.append((srv_id, port))

            ports.release()
            barrier = threading.Barrier(10)

            def _parallel_starter(srv_id: str) -> None:
                barrier.wait(timeout=10.0)
                harness.registry.start(srv_id)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(_parallel_starter, srv_id)
                    for srv_id, _ in server_configs
                ]
                for fut in futures:
                    fut.result()

            for srv_id, port in server_configs:
                assert harness.registry.wait_for_state(
                    srv_id, "running", timeout=15.0
                )
                wait_for_port("127.0.0.1", port, timeout=15.0)
                runner = harness.registry.runner_for(srv_id)
                assert isinstance(runner, ProcessServerRunner)
                assert runner.is_running() is True
                is_listening = (
                    runner.is_listening()
                    if callable(runner.is_listening)
                    else runner.is_listening
                )
                assert is_listening is True

            def _fetch_tools(port: int) -> list[str]:
                return anyio.run(
                    _mcp_list_tools, f"http://127.0.0.1:{port}/mcp"
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                tool_futures = [
                    executor.submit(_fetch_tools, port)
                    for _, port in server_configs
                ]
                results = [f.result() for f in tool_futures]

            for i, res in enumerate(results, start=1):
                assert res == [f"tool_pbarrier_{i}"]


@pytest.mark.timeout(60)
def test_mcp_process_10x_variable_namespace_isolation_under_concurrent_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """10 process servers with distinct variables, using echo gate,
    verifying 100 concurrent requests with zero cross-talk.
    """
    monkeypatch.setenv(_TEST_ECHO_VARS_ENV, "1")

    reserve = EphemeralPortReserve(10)
    ports = reserve.allocate()
    with CollectionVariablesIntegrationHarness(
        tmp_path, execution_mode="process"
    ) as harness:
        server_configs: list[tuple[str, int, str]] = []
        for i, port in enumerate(ports, start=1):
            secret = f"unique-proc-secret-{i}"
            lib_id = f"lib-piso-{i}"
            col_id = f"col-piso-{i}"
            col_data = {
                "id": col_id,
                "name": f"Collection {col_id}",
                "variables": [
                    {
                        "name": "server_index",
                        "type": "string",
                        "default": str(i),
                        "required": True,
                        "secret": False,
                    },
                    {
                        "name": "unique_secret",
                        "type": "string",
                        "default": secret,
                        "required": True,
                        "secret": False,
                    },
                ],
                "requests": [
                    {
                        "id": "get_identity",
                        "name": "get_identity",
                        "method": "GET",
                        "url": "http://127.0.0.1/get_identity",
                        "expose_as_mcp": True,
                    }
                ],
            }
            harness.create_library(
                manifest_id=lib_id,
                is_legacy_manifest=False,
                collections_data={f"{col_id}.json": col_data},
            )
            server_id = f"standalone-{lib_id}-{col_id}"
            config = McpServerConfiguration.model_construct(
                id=server_id,
                name=f"Standalone {col_id}",
                host="127.0.0.1",
                port=port,
                server_type="local",
                library_id=lib_id,
                manifest_id=lib_id,
                library_collection_path=f"collections/{col_id}.json",
                library_collection_index=0,
                environment_id=None,
                enabled=True,
            )
            harness.registry.validate_library_candidate(config)
            harness.registry.upsert(config)
            reserve.release()
            harness.registry.start(server_id)
            server_configs.append((server_id, port, secret))

        for srv_id, port, _ in server_configs:
            assert harness.registry.wait_for_state(
                srv_id, "running", timeout=15.0
            )
            wait_for_port("127.0.0.1", port, timeout=15.0)
            runner = harness.registry.runner_for(srv_id)
            assert isinstance(runner, ProcessServerRunner)

        def _call_identity(port: int) -> dict[str, str]:
            res = anyio.run(
                _mcp_call_tool,
                f"http://127.0.0.1:{port}/mcp",
                "get_identity",
                {},
            )
            body = json.loads(res.get("body", "{}"))
            return {
                "server_index": str(body.get("server_index", "")),
                "isolation_marker": str(body.get("isolation_marker", "")),
            }

        tasks: list[
            tuple[concurrent.futures.Future[dict[str, str]], int, str]
        ] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            for _ in range(10):
                for idx, (_, port, secret) in enumerate(
                    server_configs, start=1
                ):
                    tasks.append(
                        (pool.submit(_call_identity, port), idx, secret)
                    )
            for fut, expected_idx, expected_secret in tasks:
                got = fut.result()
                assert got["server_index"] == str(expected_idx)
                assert got["isolation_marker"] == expected_secret


@pytest.mark.timeout(60)
def test_mcp_process_10x_abrupt_client_disconnect_rst_resilience(
    tmp_path: Path,
) -> None:
    """10 process servers subjected to TCP RST with SO_LINGER=0,
    verifying child processes remain alive, supervisor handles disconnects cleanly,
    and subsequent requests succeed.
    """
    with reserve_ephemeral_ports(10) as ports:
        with CollectionVariablesIntegrationHarness(
            tmp_path, execution_mode="process"
        ) as harness:
            server_configs: list[tuple[str, int]] = []
            for i, port in enumerate(ports, start=1):
                srv_id = _upsert_standalone_process(
                    harness,
                    index=i,
                    port=port,
                    prefix="prst",
                    tool_name=f"tool_prst_{i}",
                )
                ports.release()
                harness.registry.start(srv_id)
                server_configs.append((srv_id, port))

            for srv_id, port in server_configs:
                assert harness.registry.wait_for_state(
                    srv_id, "running", timeout=15.0
                )
                wait_for_port("127.0.0.1", port, timeout=15.0)

            # Abrupt TCP RST disconnection mid-flight on each server
            for _, port in server_configs:
                try:
                    with socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM
                    ) as raw_sock:
                        raw_sock.connect(("127.0.0.1", port))
                        raw_sock.sendall(
                            b"POST /mcp HTTP/1.1\r\n"
                            b"Host: 127.0.0.1\r\n"
                            b"Content-Type: application/json\r\n"
                            b"Content-Length: 1000\r\n\r\n"
                            b'{"jsonrpc": "2.0", '
                        )
                        raw_sock.setsockopt(
                            socket.SOL_SOCKET,
                            socket.SO_LINGER,
                            struct.pack("ii", 1, 0),
                        )
                except OSError:
                    pass

            for srv_id, _ in server_configs:
                assert harness.registry.is_running(srv_id) is True
                runner = harness.registry.runner_for(srv_id)
                assert isinstance(runner, ProcessServerRunner)
                assert runner.is_running() is True
                assert runner.worker_is_alive() is True
                is_listening = (
                    runner.is_listening()
                    if callable(runner.is_listening)
                    else runner.is_listening
                )
                assert is_listening is True

            def _fetch_tools(port: int) -> list[str]:
                return anyio.run(
                    _mcp_list_tools, f"http://127.0.0.1:{port}/mcp"
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                tool_futures = [
                    executor.submit(_fetch_tools, port)
                    for _, port in server_configs
                ]
                results = [f.result() for f in tool_futures]

            for i, res in enumerate(results, start=1):
                assert res == [f"tool_prst_{i}"]


@pytest.mark.timeout(60)
def test_mcp_process_10x_concurrent_teardown_and_socket_reclamation(
    tmp_path: Path,
) -> None:
    """10 process servers stopped in parallel via stop_all,
    verifying all child processes terminate, ports immediately rebindable
    via verify_all_rebound and TCP probe.
    """
    reserve = EphemeralPortReserve(10)
    ports = reserve.allocate()
    with CollectionVariablesIntegrationHarness(
        tmp_path, execution_mode="process"
    ) as harness:
        server_ids: list[str] = []
        for i, port in enumerate(ports, start=1):
            srv_id = _upsert_standalone_process(
                harness,
                index=i,
                port=port,
                prefix="ptear",
                tool_name=f"tool_ptear_{i}",
            )
            reserve.release()
            harness.registry.start(srv_id)
            server_ids.append(srv_id)

        for srv_id, port in zip(server_ids, ports):
            assert harness.registry.wait_for_state(
                srv_id, "running", timeout=15.0
            )
            wait_for_port("127.0.0.1", port, timeout=15.0)

        harness.registry.stop_all(timeout=10.0, max_workers=10)

        for srv_id in server_ids:
            assert harness.registry.status(srv_id).state == "stopped"
            assert harness.registry.is_running(srv_id) is False
            runner = harness.registry.runner_for(srv_id)
            assert isinstance(runner, ProcessServerRunner)
            assert runner.worker_is_alive() is False

        assert reserve.verify_all_rebound(timeout=2.0) is True

        for port in ports:
            with socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            ) as probe_sock:
                probe_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                probe_sock.bind(("127.0.0.1", port))


@pytest.mark.timeout(30)
def test_mcp_process_windows_stop_escalation_simulate_terminate_to_kill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Simulate sys.platform == 'win32' and uncooperative worker with DEBUG_HANG,
    verifying stop escalation cleanly calls terminate() and kill(),
    logging mcp_worker_terminate and mcp_worker_kill, and exiting within stop budget.
    """
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")
    monkeypatch.setattr(sys, "platform", "win32")

    caplog.set_level(logging.WARNING)

    reserve = EphemeralPortReserve(1)
    ports = reserve.allocate()
    port = ports[0]
    with CollectionVariablesIntegrationHarness(
        tmp_path, execution_mode="process"
    ) as harness:
        server_id = _upsert_standalone_process(
            harness,
            index=1,
            port=port,
            prefix="winhang",
            tool_name="tool_winhang",
        )
        reserve.release()
        harness.registry.start(server_id)
        assert harness.registry.wait_for_state(
            server_id, "running", timeout=15.0
        )
        wait_for_port("127.0.0.1", port, timeout=15.0)

        runner = harness.registry.runner_for(server_id)
        assert isinstance(runner, ProcessServerRunner)
        supervisor = runner.supervisor
        assert isinstance(supervisor, McpProcessSupervisor)

        with supervisor._lock:
            record = supervisor._workers[server_id]
            worker_proc = record.process

        assert worker_proc is not None
        assert worker_proc.is_alive()

        orig_kill = worker_proc.kill

        terminate_called = threading.Event()
        kill_called = threading.Event()

        def _stubborn_terminate() -> None:
            terminate_called.set()
            # Stubbornly ignore terminate() so supervisor escalates to kill()

        def _escalated_kill() -> None:
            kill_called.set()
            orig_kill()

        monkeypatch.setattr(worker_proc, "terminate", _stubborn_terminate)
        monkeypatch.setattr(worker_proc, "kill", _escalated_kill)

        runner.send_debug_opcode("DEBUG_HANG")

        started = time.monotonic()
        harness.registry.stop(server_id)
        elapsed = time.monotonic() - started

        assert terminate_called.is_set(), "process.terminate() was not called"
        assert kill_called.is_set(), "process.kill() was not called"

        assert elapsed <= _STOP_BUDGET_S + 0.5, (
            f"stop exceeded budget: {elapsed:.3f}s > {_STOP_BUDGET_S}s"
        )
        assert harness.registry.status(server_id).state == "stopped"
        assert runner.worker_is_alive() is False

        # Verify supervisor logged escalation warnings
        log_messages = [rec.message for rec in caplog.records]
        assert any("mcp_worker_terminate" in msg for msg in log_messages)
        assert any("mcp_worker_kill" in msg for msg in log_messages)

        assert reserve.verify_all_rebound(timeout=2.0) is True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))
