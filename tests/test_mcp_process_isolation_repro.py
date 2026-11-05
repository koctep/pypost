"""Red acceptance tests for MCP process-mode isolation (PYPOST-1439 Step 3).

Architecture: ai-tasks/PYPOST-1439/20-architecture.md § Mandatory — Failing Repro

These tests assert desired process-mode behavior before Step 4 lands. Expected reds
today include AttributeError / ValidationError on AppSettings.mcp_execution_mode,
ImportError for ProcessServerRunner / McpProcessSupervisor, or TypeError when the
registry rejects execution_mode=.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
from pathlib import Path
import socket
import threading
import time
from typing import Any
import anyio
import pytest
from pydantic import ValidationError

from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.models.settings import AppSettings, McpServerConfiguration
from tests.helpers.collection_integration_harness import (
    CollectionVariablesIntegrationHarness,
)
from tests.helpers.mcp_live_server import wait_for_port
from tests.helpers.port_allocation import (
    EphemeralPortReserve,
    reserve_ephemeral_ports,
)
from tests.test_mcp_server_integration import _mcp_call_tool, _mcp_list_tools

pytestmark = pytest.mark.timeout(60)

# Aligned with adaptive join / evaluation §4.1 stop budget.
_STOP_BUDGET_S = 3.0

# Spawned workers cannot see parent RequestService mocks; children echo the
# variable snapshot when this env gate is set (see MCPServerImpl).
_TEST_ECHO_VARS_ENV = "PYPOST_MCP_TEST_ECHO_VARS"

# DEBUG_ABORT / DEBUG_HANG require this gate in supervisor + worker.
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


def _bind_execution_mode(
    harness: CollectionVariablesIntegrationHarness,
    mode: str,
) -> None:
    """Rebuild harness registry with mcp_execution_mode (Step 4 registry API)."""
    settings = AppSettings(mcp_execution_mode=mode)
    assert settings.mcp_execution_mode == mode
    harness.registry = MCPServerRegistry(
        library_service=harness.library_service,
        template_service=harness.template_service,
        environment_lookup=lambda _id: None,
        execution_mode=settings.mcp_execution_mode,
    )


def _upsert_standalone(
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


@pytest.mark.timeout(10)
def test_process_mode_setting_defaults_to_thread_and_accepts_process() -> None:
    """AppSettings.mcp_execution_mode defaults to thread and accepts process."""
    assert AppSettings().mcp_execution_mode == "thread"

    process_settings = AppSettings(mcp_execution_mode="process")
    assert process_settings.mcp_execution_mode == "process"

    with pytest.raises(ValidationError):
        AppSettings(mcp_execution_mode="coroutine")


@pytest.mark.timeout(10)
def test_app_settings_mcp_execution_mode_reaches_controller_registry() -> None:
    """AppSettings.mcp_execution_mode is passed into MCPServerRegistry by the UI host."""
    from unittest.mock import MagicMock

    from pypost.ui.mcp_server_controller import McpServerSettingsController

    process_settings = AppSettings(mcp_execution_mode="process")
    controller = McpServerSettingsController(
        settings_provider=lambda: process_settings,
        collection_lookup=lambda _id: None,
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
    )
    assert controller.registry._execution_mode == "process"
    assert controller.registry._process_supervisor is not None

    thread_settings = AppSettings(mcp_execution_mode="thread")
    thread_controller = McpServerSettingsController(
        settings_provider=lambda: thread_settings,
        collection_lookup=lambda _id: None,
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
    )
    assert thread_controller.registry._execution_mode == "thread"
    assert thread_controller.registry._process_supervisor is None


@pytest.mark.timeout(60)
def test_process_mode_crash_isolation_peer_servers_survive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fatal child exit fails only that instance; peer server and host survive."""
    # Step 4 symbols — ImportError is a valid red until modules exist.
    from pypost.core.mcp_process_supervisor import McpProcessSupervisor
    from pypost.core.mcp_server_runner import ProcessServerRunner

    # Must be set before spawn so the child inherits the debug-IPC gate.
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")

    host_pid = os.getpid()
    with reserve_ephemeral_ports(2) as ports:
        with CollectionVariablesIntegrationHarness(tmp_path) as harness:
            _bind_execution_mode(harness, "process")
            server_a = _upsert_standalone(
                harness,
                index=1,
                port=ports[0],
                prefix="crash",
                tool_name="tool_crash_a",
            )
            server_b = _upsert_standalone(
                harness,
                index=2,
                port=ports[1],
                prefix="crash",
                tool_name="tool_crash_b",
            )
            harness.registry.start(server_a)
            harness.registry.start(server_b)
            assert harness.registry.wait_for_state(
                server_a, "running", timeout=15.0
            )
            assert harness.registry.wait_for_state(
                server_b, "running", timeout=15.0
            )
            wait_for_port("127.0.0.1", ports[0], timeout=15.0)
            wait_for_port("127.0.0.1", ports[1], timeout=15.0)

            runner_a = harness.registry.runner_for(server_a)
            assert isinstance(runner_a, ProcessServerRunner)
            assert isinstance(
                runner_a.supervisor, McpProcessSupervisor
            )
            # Test-only IPC opcode (gated in production worker paths).
            runner_a.send_debug_opcode("DEBUG_ABORT")

            assert harness.registry.wait_for_state(
                server_a, "failed", timeout=10.0
            )
            assert os.getpid() == host_pid
            assert harness.registry.status(server_b).state == "running"
            tools_b = anyio.run(
                _mcp_list_tools, f"http://127.0.0.1:{ports[1]}/mcp"
            )
            assert tools_b == ["tool_crash_b"]


@pytest.mark.timeout(60)
def test_process_mode_variable_isolation_under_concurrent_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """10 process-mode servers keep distinct variable namespaces under load."""
    from pypost.core.mcp_server_runner import ProcessServerRunner

    # Must be set before spawn so child workers inherit the echo gate.
    monkeypatch.setenv(_TEST_ECHO_VARS_ENV, "1")

    reserve = EphemeralPortReserve(10)
    ports = reserve.allocate()
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        _bind_execution_mode(harness, "process")
        server_configs: list[tuple[str, int, str]] = []
        for i, port in enumerate(ports, start=1):
            secret = f"unique-secret-{i}"
            lib_id = f"lib-pvar-{i}"
            col_id = f"col-pvar-{i}"
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
                # Echo gate uses isolation_marker (avoids secret-key redaction).
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


@pytest.mark.timeout(30)
def test_process_mode_bounded_stop_with_unresponsive_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unresponsive process worker is force-stopped within the stop budget."""
    from pypost.core.mcp_process_supervisor import McpProcessSupervisor
    from pypost.core.mcp_server_runner import ProcessServerRunner

    # Must be set before spawn so the child inherits the debug-IPC gate.
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")

    reserve = EphemeralPortReserve(1)
    ports = reserve.allocate()
    port = ports[0]
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        _bind_execution_mode(harness, "process")
        server_id = _upsert_standalone(
            harness,
            index=1,
            port=port,
            prefix="hang",
            tool_name="tool_hang",
        )
        harness.registry.start(server_id)
        assert harness.registry.wait_for_state(
            server_id, "running", timeout=15.0
        )
        wait_for_port("127.0.0.1", port, timeout=15.0)

        runner = harness.registry.runner_for(server_id)
        assert isinstance(runner, ProcessServerRunner)
        assert isinstance(runner.supervisor, McpProcessSupervisor)
        runner.send_debug_opcode("DEBUG_HANG")

        started = time.monotonic()
        harness.registry.stop(server_id)
        elapsed = time.monotonic() - started

        assert elapsed <= _STOP_BUDGET_S + 0.5, (
            f"stop exceeded budget: {elapsed:.3f}s > {_STOP_BUDGET_S}s"
        )
        assert harness.registry.status(server_id).state == "stopped"
        assert runner.worker_is_alive() is False
        assert reserve.verify_all_rebound(timeout=2.0) is True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))


@pytest.mark.timeout(30)
def test_thread_mode_regression_still_passes_10x_barrier_startup(
    tmp_path: Path,
) -> None:
    """NFR5: default harness/registry thread path keeps 10x barrier startup green.

    Uses the same default CollectionVariablesIntegrationHarness + registry pattern
    as tests/test_mcp_multiserver_stress_10x.py (no mcp_execution_mode / execution_mode=
    yet). Must stay green on current code; only fails if Step 4 breaks thread mode.
    """
    with reserve_ephemeral_ports(10) as ports:
        with CollectionVariablesIntegrationHarness(tmp_path) as harness:
            server_configs: list[tuple[str, int]] = []
            for i, port in enumerate(ports, start=1):
                server_id = _upsert_standalone(
                    harness,
                    index=i,
                    port=port,
                    prefix="thr",
                    tool_name=f"tool_barrier_{i}",
                )
                server_configs.append((server_id, port))

            barrier = threading.Barrier(10)

            def _parallel_starter(srv_id: str) -> None:
                barrier.wait(timeout=10.0)
                harness.registry.start(srv_id)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
                futures = [
                    pool.submit(_parallel_starter, srv_id)
                    for srv_id, _ in server_configs
                ]
                for fut in futures:
                    fut.result()

            for srv_id, port in server_configs:
                assert harness.registry.wait_for_state(
                    srv_id, "running", timeout=15.0
                )
                wait_for_port("127.0.0.1", port, timeout=15.0)
                mgr = harness.registry.manager_for(srv_id)
                assert mgr.is_listening is True

            def _fetch_tools(port: int) -> list[str]:
                return anyio.run(
                    _mcp_list_tools, f"http://127.0.0.1:{port}/mcp"
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
                tool_futures = [
                    pool.submit(_fetch_tools, port)
                    for _, port in server_configs
                ]
                results = [f.result() for f in tool_futures]

            for i, res in enumerate(results, start=1):
                assert res == [f"tool_barrier_{i}"]
