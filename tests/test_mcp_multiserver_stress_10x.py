"""High-density 10+ server stress tests with abrupt disconnects and socket reclamation.

Jira: PYPOST-1438
Architecture: ai-tasks/PYPOST-1438/20-architecture.md
"""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import socket
import struct
import threading
from typing import Any
from unittest.mock import MagicMock, patch

import anyio
import pytest

from pypost.core.request_service import ExecutionResult, ResponseData
from pypost.models.settings import McpServerConfiguration
from tests.helpers.collection_integration_harness import CollectionVariablesIntegrationHarness
from tests.helpers.mcp_live_server import wait_for_port
from tests.helpers.port_allocation import (
    EphemeralPortReserve,
    reserve_ephemeral_ports,
)
from tests.test_mcp_server_integration import _mcp_call_tool, _mcp_list_tools

pytestmark = pytest.mark.timeout(60)


def _mock_result(body: str = "ok") -> ExecutionResult:
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={"content-type": "application/json"},
            body=body,
            elapsed_time=0.005,
            size=len(body),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


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


@pytest.mark.timeout(30)
def test_mcp_10x_parallel_startup_barrier_synchronization(tmp_path: Path) -> None:
    """10 standalone MCP servers launched concurrently using threading.Barrier(10),
    asserting all 10 reach running status and report is_listening == True.
    """
    with reserve_ephemeral_ports(10) as ports:
        with CollectionVariablesIntegrationHarness(tmp_path) as harness:
            server_configs: list[tuple[str, int]] = []
            for i, port in enumerate(ports, start=1):
                lib_id = f"lib-barrier-{i}"
                col_id = f"col-barrier-{i}"
                tool_name = f"tool_barrier_{i}"
                col_data = _make_collection(col_id, tool_name)
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
                server_configs.append((server_id, port))

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

            # Assert all 10 servers transition to running and report is_listening == True
            for srv_id, port in server_configs:
                assert harness.registry.wait_for_state(srv_id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", port, timeout=15.0)
                mgr = harness.registry.manager_for(srv_id)
                assert mgr.is_listening is True

            # Assert concurrent MCP tools/list requests across all 10 servers
            def _fetch_tools(port: int) -> list[str]:
                return anyio.run(_mcp_list_tools, f"http://127.0.0.1:{port}/mcp")

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                tool_futures = [
                    executor.submit(_fetch_tools, port)
                    for _, port in server_configs
                ]
                results = [f.result() for f in tool_futures]

            for i, res in enumerate(results, start=1):
                assert res == [f"tool_barrier_{i}"]


@pytest.mark.timeout(30)
def test_mcp_10x_variable_namespace_isolation_under_concurrent_load(
    tmp_path: Path,
) -> None:
    """10 servers each with distinct variable values for identical key server_id,
    receiving concurrent requests, asserting zero cross-talk across 100 requests.
    """
    reserve = EphemeralPortReserve(10)
    ports = reserve.allocate()
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        server_configs: list[tuple[str, int, str]] = []
        for i, port in enumerate(ports, start=1):
            srv_val = f"server-token-{i}"
            lib_id = f"lib-iso-{i}"
            col_id = f"col-iso-{i}"
            col_data = _make_collection(
                col_id,
                tool_name="get_identity",
                var_name="server_id",
                var_value=srv_val,
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
            harness.registry.start(server_id)
            server_configs.append((server_id, port, srv_val))

        for srv_id, port, _ in server_configs:
            assert harness.registry.wait_for_state(srv_id, "running", timeout=15.0)
            wait_for_port("127.0.0.1", port, timeout=15.0)

        with patch("pypost.core.mcp_server_impl.RequestService") as mock_service_cls:
            mock_inst = MagicMock()
            mock_service_cls.return_value = mock_inst
            mock_inst.execute.side_effect = lambda req, vars, **kw: _mock_result(
                json.dumps({"resolved_id": vars.get("server_id")})
            )

            def _call_identity(port: int) -> str:
                res = anyio.run(
                    _mcp_call_tool,
                    f"http://127.0.0.1:{port}/mcp",
                    "get_identity",
                    {},
                )
                body = json.loads(res.get("body", "{}"))
                return str(body.get("resolved_id", ""))

            # Execute 100 concurrent requests (10 rounds across 10 servers)
            tasks: list[tuple[concurrent.futures.Future[str], str]] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                for _ in range(10):
                    for _, port, expected_val in server_configs:
                        tasks.append(
                            (executor.submit(_call_identity, port), expected_val)
                        )

                for fut, expected_val in tasks:
                    assert fut.result() == expected_val


@pytest.mark.timeout(30)
def test_mcp_10x_abrupt_client_disconnect_rst_resilience(tmp_path: Path) -> None:
    """Simulated abrupt client connection termination (TCP socket abort with SO_LINGER=0 RST),
    asserting server daemon threads remain healthy, unhandled exceptions are caught,
    and servers answer subsequent valid client requests.
    """
    with reserve_ephemeral_ports(10) as ports:
        with CollectionVariablesIntegrationHarness(tmp_path) as harness:
            server_configs: list[tuple[str, int]] = []
            for i, port in enumerate(ports, start=1):
                lib_id = f"lib-rst-{i}"
                col_id = f"col-rst-{i}"
                tool_name = f"tool_rst_{i}"
                col_data = _make_collection(col_id, tool_name)
                harness.create_library(
                    manifest_id=lib_id,
                    is_legacy_manifest=False,
                    collections_data={f"{col_id}.json": col_data},
                )
                srv_id, port, status = harness.start_standalone_server(
                    manifest_id=lib_id,
                    collection_id=col_id,
                    collection_filename=f"{col_id}.json",
                    port=port,
                )
                assert status == "running"
                wait_for_port("127.0.0.1", port, timeout=15.0)
                server_configs.append((srv_id, port))

            # Simulate abrupt TCP RST disconnection mid-flight on each server
            for _, port in server_configs:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
                        raw_sock.connect(("127.0.0.1", port))
                        raw_sock.sendall(
                            b"POST /mcp HTTP/1.1\r\n"
                            b"Host: 127.0.0.1\r\n"
                            b"Content-Type: application/json\r\n"
                            b"Content-Length: 1000\r\n\r\n"
                            b'{"jsonrpc": "2.0", '
                        )
                        # Set SO_LINGER with timeout 0 to force an immediate TCP RST
                        raw_sock.setsockopt(
                            socket.SOL_SOCKET,
                            socket.SO_LINGER,
                            struct.pack("ii", 1, 0),
                        )
                except OSError:
                    pass

            # Assert all server daemon threads remain healthy and listening
            for srv_id, _ in server_configs:
                assert harness.registry.is_running(srv_id) is True
                mgr = harness.registry.manager_for(srv_id)
                assert mgr._server_thread is not None
                assert mgr._server_thread.is_alive()
                assert mgr.is_listening is True

            # Assert all 10 servers answer subsequent valid requests cleanly
            def _fetch_tools(port: int) -> list[str]:
                return anyio.run(_mcp_list_tools, f"http://127.0.0.1:{port}/mcp")

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                tool_futures = [
                    executor.submit(_fetch_tools, port)
                    for _, port in server_configs
                ]
                results = [f.result() for f in tool_futures]

            for i, res in enumerate(results, start=1):
                assert res == [f"tool_rst_{i}"]


@pytest.mark.timeout(30)
def test_mcp_10x_concurrent_teardown_and_socket_reclamation(tmp_path: Path) -> None:
    """Parallel teardown of all 10 servers, asserting all 10 ports are immediately
    re-bindable by raw TCP listening sockets with zero EADDRINUSE.
    """
    reserve = EphemeralPortReserve(10)
    ports = reserve.allocate()
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        server_ids: list[str] = []
        for i, port in enumerate(ports, start=1):
            lib_id = f"lib-tear-{i}"
            col_id = f"col-tear-{i}"
            col_data = _make_collection(col_id, f"tool_tear_{i}")
            harness.create_library(
                manifest_id=lib_id,
                is_legacy_manifest=False,
                collections_data={f"{col_id}.json": col_data},
            )
            srv_id, port, status = harness.start_standalone_server(
                manifest_id=lib_id,
                collection_id=col_id,
                collection_filename=f"{col_id}.json",
                port=port,
            )
            assert status == "running"
            wait_for_port("127.0.0.1", port, timeout=15.0)
            server_ids.append(srv_id)

        # Trigger concurrent shutdown across all 10 servers
        harness.registry.stop_all(timeout=10.0, max_workers=10)

        # Assert all servers are marked stopped and their worker threads terminated
        for srv_id in server_ids:
            assert harness.registry.status(srv_id).state == "stopped"
            assert harness.registry.is_running(srv_id) is False
            mgr = harness.registry.manager_for(srv_id)
            assert mgr._server_thread is None or not mgr._server_thread.is_alive()

        # Immediate socket rebinding: Assert all 10 ports can be immediately rebound
        # without EADDRINUSE errors
        assert reserve.verify_all_rebound(timeout=2.0) is True

        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_sock:
                probe_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                probe_sock.bind(("127.0.0.1", port))
