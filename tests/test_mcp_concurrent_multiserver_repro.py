"""Concurrent multi-server lifecycle execution and port contention repro tests.

Jira: PYPOST-1418
Architecture: ai-tasks/PYPOST-1418/20-architecture.md
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
from pathlib import Path
import socket
import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

import anyio
import pytest

from pypost.core.request_service import ExecutionResult, ResponseData
from pypost.models.settings import McpServerConfiguration
from tests.helpers.collection_integration_harness import CollectionVariablesIntegrationHarness
from tests.helpers.mcp_live_server import wait_for_port
from tests.helpers.port_allocation import allocate_tcp_port
from tests.test_mcp_server_integration import _mcp_call_tool, _mcp_list_tools

pytestmark = pytest.mark.timeout(30)


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
def test_concurrent_multi_server_startup_parallel(tmp_path: Path) -> None:
    """Validate simultaneous parallel startup of 3 standalone MCP servers."""
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        server_configs: list[tuple[str, int]] = []
        for i in range(1, 4):
            lib_id = f"lib-parallel-{i}"
            col_id = f"col-parallel-{i}"
            tool_name = f"tool_parallel_{i}"
            col_data = _make_collection(col_id, tool_name)
            harness.create_library(
                manifest_id=lib_id,
                is_legacy_manifest=False,
                collections_data={f"{col_id}.json": col_data},
            )
            port = allocate_tcp_port()
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

        barrier = threading.Barrier(3)

        def _parallel_starter(srv_id: str) -> None:
            barrier.wait(timeout=5.0)
            harness.registry.start(srv_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(_parallel_starter, srv_id)
                for srv_id, _ in server_configs
            ]
            for fut in futures:
                fut.result()

        # Assert all 3 servers transition to running and start listening
        for srv_id, port in server_configs:
            assert harness.registry.wait_for_state(srv_id, "running", timeout=10.0)
            wait_for_port("127.0.0.1", port, timeout=10.0)
            mgr = harness.registry.manager_for(srv_id)
            assert mgr.is_listening is True

        # Assert concurrent MCP tools/list requests across all 3 servers
        def _fetch_tools(port: int) -> list[str]:
            return anyio.run(_mcp_list_tools, f"http://127.0.0.1:{port}/mcp")

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            tool_futures = [
                executor.submit(_fetch_tools, port)
                for _, port in server_configs
            ]
            results = [f.result() for f in tool_futures]

        assert results[0] == ["tool_parallel_1"]
        assert results[1] == ["tool_parallel_2"]
        assert results[2] == ["tool_parallel_3"]


@pytest.mark.timeout(30)
def test_shared_and_overlapping_collection_variables_isolation(tmp_path: Path) -> None:
    """Validate 3 servers with overlapping variable names resolve in complete isolation."""
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        servers = [
            ("alpha", "https://alpha.internal.net"),
            ("beta", "https://beta.internal.net"),
            ("gamma", "https://gamma.internal.net"),
        ]
        active_servers: list[tuple[str, int, str]] = []
        for name, base_url in servers:
            lib_id = f"lib-{name}"
            col_id = f"col-{name}"
            col_data = _make_collection(
                col_id,
                tool_name="get_config",
                var_name="base_url",
                var_value=base_url,
            )
            harness.create_library(
                manifest_id=lib_id,
                is_legacy_manifest=False,
                collections_data={f"{col_id}.json": col_data},
            )
            srv_id, port, status = harness.start_standalone_server(
                manifest_id=lib_id,
                collection_id=col_id,
                collection_filename=f"{col_id}.json",
            )
            assert status == "running"
            wait_for_port("127.0.0.1", port, timeout=10.0)
            active_servers.append((srv_id, port, base_url))

        # Mock RequestService across all servers to echo the resolved base_url
        with patch("pypost.core.mcp_server_impl.RequestService") as mock_service_cls:
            mock_inst = MagicMock()
            mock_service_cls.return_value = mock_inst
            mock_inst.execute.side_effect = lambda req, vars, **kw: _mock_result(
                json.dumps({"resolved_base_url": vars.get("base_url")})
            )

            def _call_config(port: int) -> str:
                res = anyio.run(_mcp_call_tool, f"http://127.0.0.1:{port}/mcp", "get_config", {})
                body = json.loads(res.get("body", "{}"))
                return str(body.get("resolved_base_url", ""))

            # Concurrently fire requests to all 3 servers
            tasks: list[tuple[concurrent.futures.Future[str], str]] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                for _ in range(10):
                    for _, port, expected_url in active_servers:
                        tasks.append((executor.submit(_call_config, port), expected_url))

                for fut, expected_url in tasks:
                    assert fut.result() == expected_url


@pytest.mark.timeout(30)
def test_concurrent_hot_reload_under_active_execution(tmp_path: Path) -> None:
    """Hot-reload server 1 with modified variables while servers 2 and 3 execute
    calls concurrently.
    """
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        servers = [
            ("srv1", "https://srv1-v1.example"),
            ("srv2", "https://srv2.example"),
            ("srv3", "https://srv3.example"),
        ]
        ports: dict[str, int] = {}
        server_ids: dict[str, str] = {}
        for name, base_url in servers:
            lib_id = f"lib-{name}"
            col_id = f"col-{name}"
            col_data = _make_collection(
                col_id,
                tool_name="get_config",
                var_name="base_url",
                var_value=base_url,
            )
            harness.create_library(
                manifest_id=lib_id,
                is_legacy_manifest=False,
                collections_data={f"{col_id}.json": col_data},
            )
            srv_id, port, status = harness.start_standalone_server(
                manifest_id=lib_id,
                collection_id=col_id,
                collection_filename=f"{col_id}.json",
            )
            assert status == "running"
            wait_for_port("127.0.0.1", port, timeout=10.0)
            ports[name] = port
            server_ids[name] = srv_id

        with patch("pypost.core.mcp_server_impl.RequestService") as mock_service_cls:
            mock_inst = MagicMock()
            mock_service_cls.return_value = mock_inst
            mock_inst.execute.side_effect = lambda req, vars, **kw: _mock_result(
                json.dumps({"resolved_base_url": vars.get("base_url")})
            )

            stop_load = threading.Event()
            load_errors: list[str] = []
            call_counts: dict[str, int] = {"srv2": 0, "srv3": 0}

            def _background_worker(key: str, port: int, expected_url: str) -> None:
                while not stop_load.is_set():
                    try:
                        res = anyio.run(
                            _mcp_call_tool,
                            f"http://127.0.0.1:{port}/mcp",
                            "get_config",
                            {},
                        )
                        body = json.loads(res.get("body", "{}"))
                        if body.get("resolved_base_url") != expected_url:
                            load_errors.append(
                                f"Unexpected base_url on {key}: {body.get('resolved_base_url')}"
                            )
                        call_counts[key] += 1
                    except Exception as exc:
                        load_errors.append(f"Call failed on {key}: {exc}")
                    time.sleep(0.01)

            t2 = threading.Thread(
                target=_background_worker,
                args=("srv2", ports["srv2"], "https://srv2.example"),
                daemon=True,
            )
            t3 = threading.Thread(
                target=_background_worker,
                args=("srv3", ports["srv3"], "https://srv3.example"),
                daemon=True,
            )
            t2.start()
            t3.start()

            try:
                # Update collection file on disk with modified variable for Server 1
                new_col_data = _make_collection(
                    "col-srv1",
                    tool_name="get_config",
                    var_name="base_url",
                    var_value="https://srv1-v2.example",
                )
                col_file = harness.libraries_dir / "lib-srv1" / "collections" / "col-srv1.json"
                col_file.write_text(json.dumps(new_col_data, indent=2), encoding="utf-8")

                # Perform hot-reload reconfiguration on Server 1
                srv1_id = server_ids["srv1"]
                cfg1 = harness.registry.configuration(srv1_id)
                assert cfg1 is not None
                harness.registry.reconfigure(srv1_id, cfg1)

                # Wait for reconfiguration to complete
                assert harness.registry.wait_for_state(srv1_id, "running", timeout=10.0)
                wait_for_port("127.0.0.1", ports["srv1"], timeout=10.0)

                # Verify Server 1 now resolves the updated variable
                res1 = anyio.run(
                    _mcp_call_tool,
                    f"http://127.0.0.1:{ports['srv1']}/mcp",
                    "get_config",
                    {},
                )
                body1 = json.loads(res1.get("body", "{}"))
                assert body1.get("resolved_base_url") == "https://srv1-v2.example"
            finally:
                stop_load.set()
                t2.join(timeout=5.0)
                t3.join(timeout=5.0)

            # Assert background requests experienced zero failures or regressions
            assert not load_errors, f"Encountered errors during active load: {load_errors}"
            assert call_counts["srv2"] > 0
            assert call_counts["srv3"] > 0


@pytest.mark.timeout(30)
def test_port_collision_detection_and_graceful_recovery(
    caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """Deliberately allocate an occupied port, asserting graceful failure without crashing peers."""
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        # Start Server 1 on an allocated port
        col1_data = _make_collection("col-1", "tool_1")
        harness.create_library(
            manifest_id="lib-1",
            is_legacy_manifest=False,
            collections_data={"col-1.json": col1_data},
        )
        srv1_id, port1, status1 = harness.start_standalone_server(
            manifest_id="lib-1",
            collection_id="col-1",
            collection_filename="col-1.json",
        )
        assert status1 == "running"
        wait_for_port("127.0.0.1", port1, timeout=10.0)

        # Allocate a port and occupy it with an external raw socket
        occupied_port = allocate_tcp_port()
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_sock.bind(("127.0.0.1", occupied_port))
        raw_sock.listen(1)

        try:
            # Create Server 2 attempting to bind to the occupied port
            col2_data = _make_collection("col-2", "tool_2")
            harness.create_library(
                manifest_id="lib-2",
                is_legacy_manifest=False,
                collections_data={"col-2.json": col2_data},
            )
            srv2_id = "standalone-lib-2-col-2"
            cfg2 = McpServerConfiguration.model_construct(
                id=srv2_id,
                name="Standalone col-2",
                host="127.0.0.1",
                port=occupied_port,
                server_type="local",
                library_id="lib-2",
                manifest_id="lib-2",
                library_collection_path="collections/col-2.json",
                library_collection_index=0,
                environment_id=None,
                enabled=True,
            )
            harness.registry.validate_library_candidate(cfg2)
            harness.registry.upsert(cfg2)

            with caplog.at_level(logging.ERROR, logger="pypost.core.qt.mcp_server"):
                harness.registry.start(srv2_id)

                # Wait for Server 2 to transition to failed state
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    if harness.registry.status(srv2_id).state == "failed":
                        break
                    time.sleep(0.05)

                srv2_status = harness.registry.status(srv2_id)
                assert srv2_status.state == "failed"
                assert (
                    "could not bind" in srv2_status.message.lower()
                    or str(occupied_port) in srv2_status.message
                )

            # Assert caplog captured the bind failure error per do-testing contract
            assert any(
                "mcp_server_start_failed" in r.message and str(occupied_port) in r.message
                for r in caplog.records
            )

            # Assert Server 1 is still running and serving requests unharmed
            assert harness.registry.status(srv1_id).state == "running"
            tools1 = anyio.run(_mcp_list_tools, f"http://127.0.0.1:{port1}/mcp")
            assert tools1 == ["tool_1"]

        finally:
            raw_sock.close()

        # Recovery: Reconfigure Server 2 on a newly allocated free port
        free_port = allocate_tcp_port()
        cfg2_recovered = cfg2.model_copy(update={"port": free_port})
        harness.registry.upsert(cfg2_recovered)
        harness.registry.start(srv2_id)

        assert harness.registry.wait_for_state(srv2_id, "running", timeout=10.0)
        wait_for_port("127.0.0.1", free_port, timeout=10.0)
        assert harness.registry.status(srv2_id).state == "running"
        tools2 = anyio.run(_mcp_list_tools, f"http://127.0.0.1:{free_port}/mcp")
        assert tools2 == ["tool_2"]

        # Both servers are alive and operational
        assert harness.registry.is_running(srv1_id) is True
        assert harness.registry.is_running(srv2_id) is True


@pytest.mark.timeout(30)
def test_concurrent_multi_server_teardown_and_socket_hygiene(tmp_path: Path) -> None:
    """Concurrent multi-server shutdown, asserting clean thread termination and
    immediate re-bind.
    """
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        server_ids: list[str] = []
        ports: list[int] = []
        for i in range(1, 4):
            lib_id = f"lib-hygiene-{i}"
            col_id = f"col-hygiene-{i}"
            col_data = _make_collection(col_id, f"tool_{i}")
            harness.create_library(
                manifest_id=lib_id,
                is_legacy_manifest=False,
                collections_data={f"{col_id}.json": col_data},
            )
            srv_id, port, status = harness.start_standalone_server(
                manifest_id=lib_id,
                collection_id=col_id,
                collection_filename=f"{col_id}.json",
            )
            assert status == "running"
            wait_for_port("127.0.0.1", port, timeout=10.0)
            server_ids.append(srv_id)
            ports.append(port)

        # Trigger concurrent shutdown across all 3 servers
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            stop_futures = [
                executor.submit(harness.registry.stop, srv_id)
                for srv_id in server_ids
            ]
            for fut in stop_futures:
                fut.result()

        # Assert all servers are marked stopped and their worker threads terminated
        for srv_id in server_ids:
            assert harness.registry.status(srv_id).state == "stopped"
            assert harness.registry.is_running(srv_id) is False
            mgr = harness.registry.manager_for(srv_id)
            assert mgr._server_thread is None or not mgr._server_thread.is_alive()

        # Immediate socket rebinding: Assert OS ports were immediately released and can be bound
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_sock:
                probe_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                probe_sock.bind(("127.0.0.1", port))

        # Restart servers on the exact same ports to verify clean re-launch
        for srv_id in server_ids:
            harness.registry.start(srv_id)

        for srv_id, port in zip(server_ids, ports):
            assert harness.registry.wait_for_state(srv_id, "running", timeout=10.0)
            wait_for_port("127.0.0.1", port, timeout=10.0)
            assert harness.registry.is_running(srv_id) is True
