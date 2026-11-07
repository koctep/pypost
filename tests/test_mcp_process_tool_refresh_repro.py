"""Red acceptance tests for process-mode live collection tool refresh (PYPOST-1465).

Covers:
- Live tool addition, modification, and removal in process mode without worker restart
- Collection-scoped variable and secret refresh while preserving active environment overrides
- Isolation of neighboring collection servers and proxy servers during refresh
- Failure containment for exited workers and runner start_snapshot synchronization
- Shared-mode (thread) collection refresh parity including in-place request edits
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.mcp_server_runner import ProcessServerRunner
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import McpServerConfiguration
from tests.helpers.collection_integration_harness import (
    CollectionVariablesIntegrationHarness,
)
from tests.helpers.mcp_live_server import wait_for_port
from tests.helpers.port_allocation import reserve_ephemeral_ports
from tests.test_mcp_server_integration import _mcp_call_tool, _mcp_list_tools

pytestmark = pytest.mark.timeout(60)

_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


def wait_until(
    predicate: Callable[[], bool],
    *,
    timeout: float = 5.0,
    interval: float = 0.05,
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


async def _mcp_list_tool_details(mcp_url: str) -> dict[str, str]:
    """Return mapping of tool name -> description from a live MCP endpoint."""
    async with create_mcp_http_client() as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return {
                    tool.name: (tool.description or "") for tool in result.tools
                }


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
        do_PUT = _handle
        do_DELETE = _handle

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
    port = int(httpd.server_address[1])
    thread = threading.Thread(
        target=httpd.serve_forever,
        name=f"echo-http-{port}",
        daemon=True,
    )
    thread.start()
    try:
        yield port, recorded
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2.0)


def _worker_pid(runner: ProcessServerRunner) -> int | None:
    """Return the current child process PID for a ProcessServerRunner."""
    record = runner.supervisor._workers.get(runner.worker_id)
    if record is None or record.process is None:
        return None
    return record.process.pid


@pytest.mark.timeout(60)
def test_process_mode_refresh_collection_updates_tools_live_add_modify_remove(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Process-mode server updates exposed tools on refresh_collection without restart."""
    with _local_echo_http_server() as (stub_port, _recorded):
        with reserve_ephemeral_ports(1) as ports:
            mcp_port = ports[0]
            mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"
            collection = Collection(
                id="col-live-tools",
                name="Live Tools Collection",
                requests=[
                    RequestData(
                        id="req-alpha",
                        name="Get Alpha",
                        method="GET",
                        url=f"http://127.0.0.1:{stub_port}/v1/alpha",
                        mcp_description="Initial Alpha description",
                        expose_as_mcp=True,
                    ),
                    RequestData(
                        id="req-beta",
                        name="Get Beta",
                        method="GET",
                        url=f"http://127.0.0.1:{stub_port}/v1/beta",
                        mcp_description="Initial Beta description",
                        expose_as_mcp=True,
                    ),
                ],
            )
            environment = Environment(id="env-live", name="Live Env", variables={})
            collections = {collection.id: collection}
            environments = {environment.id: environment}
            registry = MCPServerRegistry(
                collection_lookup=collections.get,
                environment_lookup=environments.get,
                execution_mode="process",
            )
            config = McpServerConfiguration(
                id="proc-live-srv",
                host="127.0.0.1",
                port=mcp_port,
                collection_id=collection.id,
                environment_id=environment.id,
                enabled=True,
            )
            try:
                registry.upsert(config)
                registry.start(config.id)
                assert registry.wait_for_state(config.id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", mcp_port, timeout=15.0)

                runner = registry.runner_for(config.id)
                assert isinstance(runner, ProcessServerRunner)
                initial_pid = _worker_pid(runner)
                assert initial_pid is not None

                initial_details = anyio.run(_mcp_list_tool_details, mcp_url)
                assert sorted(initial_details.keys()) == ["get_alpha", "get_beta"]
                assert "Initial Alpha description" in initial_details["get_alpha"]
                assert "Initial Beta description" in initial_details["get_beta"]

                alpha_v1 = anyio.run(_mcp_call_tool, mcp_url, "get_alpha", {})
                assert json.loads(alpha_v1["body"])["path"] == "/v1/alpha"

                # Mutate collection: modify Alpha, remove Beta, add Gamma.
                collection.requests = [
                    RequestData(
                        id="req-alpha",
                        name="Get Alpha",
                        method="GET",
                        url=f"http://127.0.0.1:{stub_port}/v2/alpha-updated",
                        mcp_description="Updated Alpha description",
                        expose_as_mcp=True,
                    ),
                    RequestData(
                        id="req-gamma",
                        name="Get Gamma",
                        method="POST",
                        url=f"http://127.0.0.1:{stub_port}/v1/gamma-new",
                        mcp_description="Added Gamma description",
                        expose_as_mcp=True,
                    ),
                ]

                with caplog.at_level(
                    logging.DEBUG, logger="pypost.core.mcp_process_supervisor"
                ):
                    registry.refresh_collection(collection.id)

                    wait_until(
                        lambda: sorted(anyio.run(_mcp_list_tools, mcp_url))
                        == ["get_alpha", "get_gamma"],
                        timeout=2.0,
                        description="process worker tools/list update",
                    )

                assert any(
                    "mcp_worker_update_tools_sent instance_id=proc-live-srv "
                    "tool_count=2" in rec.message
                    for rec in caplog.records
                )
                assert "Updated Alpha description" not in caplog.text
                assert "/v2/alpha-updated" not in caplog.text

                updated_details = anyio.run(_mcp_list_tool_details, mcp_url)
                assert sorted(updated_details.keys()) == ["get_alpha", "get_gamma"]
                assert "Updated Alpha description" in updated_details["get_alpha"]
                assert "Added Gamma description" in updated_details["get_gamma"]

                alpha_v2 = anyio.run(_mcp_call_tool, mcp_url, "get_alpha", {})
                assert json.loads(alpha_v2["body"])["path"] == "/v2/alpha-updated"

                gamma_v1 = anyio.run(_mcp_call_tool, mcp_url, "get_gamma", {})
                gamma_body = json.loads(gamma_v1["body"])
                assert gamma_body["path"] == "/v1/gamma-new"
                assert gamma_body["method"] == "POST"

                # Endpoint identity and worker PID must be preserved without restart.
                assert registry.status(config.id).state == "running"
                assert registry.runner_for(config.id) is runner
                assert _worker_pid(runner) == initial_pid
            finally:
                registry.stop_all()


@pytest.mark.timeout(60)
def test_process_mode_refresh_collection_updates_collection_variables_and_preserves_env(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Refreshing a collection updates collection variables and secret masking while keeping env."""
    with _local_echo_http_server() as (stub_port, recorded):
        with reserve_ephemeral_ports(2) as ports:
            ws_port, lib_port = ports[0], ports[1]
            ws_url = f"http://127.0.0.1:{ws_port}/mcp"
            lib_url = f"http://127.0.0.1:{lib_port}/mcp"

            collection = Collection(
                id="col-vars",
                name="Vars Collection",
                variables=[
                    CollectionVariable(
                        name="col_stage",
                        type="string",
                        default="v1-col",
                        required=True,
                        secret=False,
                    ),
                    CollectionVariable(
                        name="shared_key",
                        type="string",
                        default="from-collection-v1",
                        required=True,
                        secret=False,
                    ),
                    CollectionVariable(
                        name="col_token",
                        type="string",
                        default="secret-col-token-v1",
                        required=False,
                        secret=True,
                    ),
                ],
                requests=[
                    RequestData(
                        id="req-probe",
                        name="Probe Vars",
                        method="GET",
                        url=(
                            f"http://127.0.0.1:{stub_port}"
                            "/{{ col_stage }}/{{ shared_key }}/{{ env_only }}"
                        ),
                        headers={"X-Col-Token": "{{ col_token }}"},
                        expose_as_mcp=True,
                    )
                ],
            )
            environment = Environment(
                id="env-active",
                name="Active Env",
                variables={
                    "shared_key": "from-active-env",
                    "env_only": "env-preserved",
                },
                hidden_keys=set(),
            )
            collections = {collection.id: collection}
            environments = {environment.id: environment}

            harness = CollectionVariablesIntegrationHarness(tmp_path)
            try:
                harness.registry = MCPServerRegistry(
                    collection_lookup=collections.get,
                    environment_lookup=environments.get,
                    library_service=harness.library_service,
                    template_service=harness.template_service,
                    execution_mode="process",
                )
                registry = harness.registry

                # 1. Workspace-backed server bound to col-vars + env-active
                ws_config = McpServerConfiguration(
                    id="ws-vars-srv",
                    host="127.0.0.1",
                    port=ws_port,
                    collection_id=collection.id,
                    environment_id=environment.id,
                    enabled=True,
                )
                registry.upsert(ws_config)

                # 2. Library-backed standalone server bound to col-lib-vars + env-active
                lib_id = "lib-vars-refresh"
                lib_col_id = "col-lib-vars"
                lib_col_dir = harness.create_library(
                    manifest_id=lib_id,
                    is_legacy_manifest=False,
                    collections_data={
                        f"{lib_col_id}.json": {
                            "id": lib_col_id,
                            "name": "Lib Vars Collection",
                            "variables": [
                                {
                                    "name": "lib_stage",
                                    "type": "string",
                                    "default": "lib-v1",
                                    "required": True,
                                    "secret": False,
                                },
                                {
                                    "name": "shared_key",
                                    "type": "string",
                                    "default": "from-lib-v1",
                                    "required": True,
                                    "secret": False,
                                },
                            ],
                            "requests": [
                                {
                                    "id": "lib-probe",
                                    "name": "Lib Probe",
                                    "method": "GET",
                                    "url": (
                                        f"http://127.0.0.1:{stub_port}"
                                        "/{{ lib_stage }}/{{ shared_key }}"
                                    ),
                                    "expose_as_mcp": True,
                                }
                            ],
                        }
                    },
                )
                lib_config = McpServerConfiguration.model_construct(
                    id="lib-vars-srv",
                    name="Lib Vars Server",
                    host="127.0.0.1",
                    port=lib_port,
                    server_type="local",
                    library_id=lib_id,
                    manifest_id=lib_id,
                    library_collection_path=f"collections/{lib_col_id}.json",
                    library_collection_index=0,
                    environment_id=environment.id,
                    enabled=True,
                )
                registry.validate_library_candidate(lib_config)
                registry.upsert(lib_config)

                registry.start(ws_config.id)
                registry.start(lib_config.id)
                assert registry.wait_for_state(ws_config.id, "running", timeout=15.0)
                assert registry.wait_for_state(lib_config.id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", ws_port, timeout=15.0)
                wait_for_port("127.0.0.1", lib_port, timeout=15.0)

                # Update workspace collection variables: new default, new secret value
                collection.variables = [
                    CollectionVariable(
                        name="col_stage",
                        type="string",
                        default="v2-col-refreshed",
                        required=True,
                        secret=False,
                    ),
                    CollectionVariable(
                        name="shared_key",
                        type="string",
                        default="from-collection-v2",
                        required=True,
                        secret=False,
                    ),
                    CollectionVariable(
                        name="col_token",
                        type="string",
                        default="secret-col-token-v2-rotated",
                        required=False,
                        secret=True,
                    ),
                ]
                with caplog.at_level(
                    logging.INFO, logger="pypost.core.mcp_server_registry"
                ):
                    registry.refresh_collection(collection.id)

                assert any(
                    "mcp_registry_collection_refreshed instance_id=ws-vars-srv "
                    "collection_id=col-vars execution_mode=process tool_count=1 "
                    "variable_count=4 hidden_key_count=1" in rec.message
                    for rec in caplog.records
                )
                assert "secret-col-token-v1" not in caplog.text
                assert "secret-col-token-v2-rotated" not in caplog.text
                assert "v2-col-refreshed" not in caplog.text
                assert "from-active-env" not in caplog.text

                def _ws_updated() -> bool:
                    res = anyio.run(_mcp_call_tool, ws_url, "probe_vars", {})
                    return "/v2-col-refreshed/from-active-env/env-preserved" in res.get(
                        "body", ""
                    )

                wait_until(
                    _ws_updated,
                    timeout=2.0,
                    description="workspace collection variable refresh in process worker",
                )
                ws_res = anyio.run(_mcp_call_tool, ws_url, "probe_vars", {})
                assert "/v2-col-refreshed/from-active-env/env-preserved" in ws_res["body"]
                # Secret value must be sent to upstream HTTP but redacted from MCP tool output.
                assert "secret-col-token-v2-rotated" not in ws_res["body"]
                assert any(
                    entry["headers"].get("x-col-token") == "secret-col-token-v2-rotated"
                    for entry in recorded
                )

                # Update library-backed collection on disk and refresh by collection ID.
                lib_col_file = lib_col_dir / "collections" / f"{lib_col_id}.json"
                lib_col_file.write_text(
                    json.dumps(
                        {
                            "id": lib_col_id,
                            "name": "Lib Vars Collection",
                            "variables": [
                                {
                                    "name": "lib_stage",
                                    "type": "string",
                                    "default": "lib-v2-refreshed",
                                    "required": True,
                                    "secret": False,
                                },
                                {
                                    "name": "shared_key",
                                    "type": "string",
                                    "default": "from-lib-v2",
                                    "required": True,
                                    "secret": False,
                                },
                            ],
                            "requests": [
                                {
                                    "id": "lib-probe",
                                    "name": "Lib Probe",
                                    "method": "GET",
                                    "url": (
                                        f"http://127.0.0.1:{stub_port}"
                                        "/{{ lib_stage }}/{{ shared_key }}"
                                    ),
                                    "expose_as_mcp": True,
                                },
                                {
                                    "id": "lib-extra",
                                    "name": "Lib Extra",
                                    "method": "GET",
                                    "url": f"http://127.0.0.1:{stub_port}/lib-extra",
                                    "expose_as_mcp": True,
                                },
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                registry.refresh_collection(lib_col_id)

                wait_until(
                    lambda: sorted(anyio.run(_mcp_list_tools, lib_url))
                    == ["lib_extra", "lib_probe"],
                    timeout=2.0,
                    description="library-backed collection tool and variable refresh",
                )
                lib_res = anyio.run(_mcp_call_tool, lib_url, "lib_probe", {})
                assert "/lib-v2-refreshed/from-active-env" in lib_res["body"]
            finally:
                harness.teardown()


@pytest.mark.timeout(60)
def test_process_mode_refresh_collection_isolates_neighbor_and_proxy_servers() -> None:
    """Refreshing one collection leaves neighbor and proxy servers untouched."""
    with reserve_ephemeral_ports(3) as ports:
        target_port, neighbor_port, proxy_port = ports[0], ports[1], ports[2]
        target_url = f"http://127.0.0.1:{target_port}/mcp"
        neighbor_url = f"http://127.0.0.1:{neighbor_port}/mcp"
        proxy_url = f"http://127.0.0.1:{proxy_port}/mcp"

        col_target = Collection(
            id="col-target",
            requests=[
                RequestData(
                    id="t-1",
                    name="target_v1",
                    method="GET",
                    url="http://127.0.0.1/t1",
                    expose_as_mcp=True,
                )
            ],
        )
        col_neighbor = Collection(
            id="col-neighbor",
            requests=[
                RequestData(
                    id="n-1",
                    name="neighbor_tool",
                    method="GET",
                    url="http://127.0.0.1/n1",
                    expose_as_mcp=True,
                )
            ],
        )
        env = Environment(id="env-iso", variables={})
        collections = {col_target.id: col_target, col_neighbor.id: col_neighbor}
        registry = MCPServerRegistry(
            collection_lookup=collections.get,
            environment_lookup=lambda _id: env,
            execution_mode="process",
        )
        registry.upsert(
            McpServerConfiguration(
                id="srv-target",
                host="127.0.0.1",
                port=target_port,
                collection_id=col_target.id,
                environment_id=env.id,
                enabled=True,
            )
        )
        registry.upsert(
            McpServerConfiguration(
                id="srv-neighbor",
                host="127.0.0.1",
                port=neighbor_port,
                collection_id=col_neighbor.id,
                environment_id=env.id,
                enabled=True,
            )
        )
        registry.upsert(
            McpServerConfiguration(
                id="srv-proxy",
                host="127.0.0.1",
                port=proxy_port,
                server_type="proxy",
                upstream_url=neighbor_url,
                upstream_transport="streamable_http",
                environment_id=env.id,
                enabled=True,
            )
        )
        try:
            registry.start("srv-target")
            registry.start("srv-neighbor")
            registry.start("srv-proxy")
            for srv_id, port in (
                ("srv-target", target_port),
                ("srv-neighbor", neighbor_port),
                ("srv-proxy", proxy_port),
            ):
                assert registry.wait_for_state(srv_id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", port, timeout=15.0)

            target_runner = registry.runner_for("srv-target")
            neighbor_runner = registry.runner_for("srv-neighbor")
            proxy_runner = registry.runner_for("srv-proxy")
            assert isinstance(target_runner, ProcessServerRunner)
            assert isinstance(neighbor_runner, ProcessServerRunner)
            assert isinstance(proxy_runner, ProcessServerRunner)
            target_pid = _worker_pid(target_runner)
            neighbor_pid = _worker_pid(neighbor_runner)
            proxy_pid = _worker_pid(proxy_runner)

            assert anyio.run(_mcp_list_tools, target_url) == ["target_v1"]
            assert anyio.run(_mcp_list_tools, neighbor_url) == ["neighbor_tool"]
            assert anyio.run(_mcp_list_tools, proxy_url) == ["neighbor_tool"]

            # Mutate both in-memory collections, but refresh ONLY col-target.
            col_target.requests = [
                RequestData(
                    id="t-2",
                    name="target_v2",
                    method="GET",
                    url="http://127.0.0.1/t2",
                    expose_as_mcp=True,
                )
            ]
            col_neighbor.requests = [
                RequestData(
                    id="n-2",
                    name="unrefresh_neighbor_tool",
                    method="GET",
                    url="http://127.0.0.1/n2",
                    expose_as_mcp=True,
                )
            ]

            registry.refresh_collection(col_target.id)

            wait_until(
                lambda: anyio.run(_mcp_list_tools, target_url) == ["target_v2"],
                timeout=2.0,
                description="target collection server tool refresh",
            )
            assert anyio.run(_mcp_list_tools, neighbor_url) == ["neighbor_tool"]
            assert anyio.run(_mcp_list_tools, proxy_url) == ["neighbor_tool"]

            assert _worker_pid(target_runner) == target_pid
            assert _worker_pid(neighbor_runner) == neighbor_pid
            assert _worker_pid(proxy_runner) == proxy_pid
            assert registry.status("srv-target").state == "running"
            assert registry.status("srv-neighbor").state == "running"
            assert registry.status("srv-proxy").state == "running"
        finally:
            registry.stop_all()


@pytest.mark.timeout(60)
def test_process_mode_refresh_collection_contains_exited_worker_and_updates_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Refreshing a collection when one worker has exited marks it failed and updates peers."""
    monkeypatch.setenv(_ALLOW_DEBUG_IPC_ENV, "1")

    with reserve_ephemeral_ports(2) as ports:
        dead_port, healthy_port = ports[0], ports[1]
        healthy_url = f"http://127.0.0.1:{healthy_port}/mcp"

        collection = Collection(
            id="col-shared",
            requests=[
                RequestData(
                    id="s-1",
                    name="shared_v1",
                    method="GET",
                    url="http://127.0.0.1/s1",
                    expose_as_mcp=True,
                )
            ],
        )
        env = Environment(id="env-shared", variables={"env_k": "env_v"})
        collections = {collection.id: collection}
        registry = MCPServerRegistry(
            collection_lookup=collections.get,
            environment_lookup=lambda _id: env,
            execution_mode="process",
        )
        registry.upsert(
            McpServerConfiguration(
                id="srv-dead",
                host="127.0.0.1",
                port=dead_port,
                collection_id=collection.id,
                environment_id=env.id,
                enabled=True,
            )
        )
        registry.upsert(
            McpServerConfiguration(
                id="srv-healthy",
                host="127.0.0.1",
                port=healthy_port,
                collection_id=collection.id,
                environment_id=env.id,
                enabled=True,
            )
        )
        try:
            registry.start("srv-dead")
            registry.start("srv-healthy")
            assert registry.wait_for_state("srv-dead", "running", timeout=15.0)
            assert registry.wait_for_state("srv-healthy", "running", timeout=15.0)
            wait_for_port("127.0.0.1", dead_port, timeout=15.0)
            wait_for_port("127.0.0.1", healthy_port, timeout=15.0)

            dead_runner = registry.runner_for("srv-dead")
            healthy_runner = registry.runner_for("srv-healthy")
            assert isinstance(dead_runner, ProcessServerRunner)
            assert isinstance(healthy_runner, ProcessServerRunner)

            # Force srv-dead child worker to exit before refresh_collection runs.
            with caplog.at_level(
                logging.ERROR, logger="pypost.core.mcp_server_registry"
            ):
                dead_runner.send_debug_opcode("DEBUG_ABORT")
                wait_until(
                    lambda: not dead_runner.worker_is_alive(),
                    timeout=5.0,
                    description="srv-dead worker exit",
                )

                collection.requests = [
                    RequestData(
                        id="s-2",
                        name="shared_v2",
                        method="GET",
                        url="http://127.0.0.1/s2",
                        expose_as_mcp=True,
                    )
                ]

                # Must not raise even though srv-dead's worker has exited.
                registry.refresh_collection(collection.id)
                assert registry.wait_for_state("srv-dead", "failed", timeout=5.0)

            assert any(
                "mcp_registry_unexpected_child_exit" in record.message
                or "srv-dead" in record.message
                for record in caplog.records
            )
            assert registry.status("srv-healthy").state == "running"

            wait_until(
                lambda: anyio.run(_mcp_list_tools, healthy_url) == ["shared_v2"],
                timeout=2.0,
                description="healthy peer tools/list refresh",
            )
            assert [t.name for t in healthy_runner.start_snapshot.tools] == [
                "shared_v2"
            ]
        finally:
            registry.stop_all()


@pytest.mark.timeout(60)
def test_shared_mode_refresh_collection_regression_parity() -> None:
    """Shared thread-mode refresh_collection updates request edits and tool additions/removals."""
    with _local_echo_http_server() as (stub_port, _recorded):
        with reserve_ephemeral_ports(1) as ports:
            mcp_port = ports[0]
            mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"
            collection = Collection(
                id="col-thread-parity",
                requests=[
                    RequestData(
                        id="req-1",
                        name="Thread Alpha",
                        method="GET",
                        url=f"http://127.0.0.1:{stub_port}/v1/thread-alpha",
                        mcp_description="Thread Alpha v1",
                        expose_as_mcp=True,
                    ),
                    RequestData(
                        id="req-2",
                        name="Thread Beta",
                        method="GET",
                        url=f"http://127.0.0.1:{stub_port}/v1/thread-beta",
                        mcp_description="Thread Beta v1",
                        expose_as_mcp=True,
                    ),
                ],
            )
            env = Environment(id="env-thread", variables={})
            collections = {collection.id: collection}
            registry = MCPServerRegistry(
                collection_lookup=collections.get,
                environment_lookup=lambda _id: env,
                execution_mode="thread",
            )
            config = McpServerConfiguration(
                id="thr-parity-srv",
                host="127.0.0.1",
                port=mcp_port,
                collection_id=collection.id,
                environment_id=env.id,
                enabled=True,
            )
            try:
                registry.upsert(config)
                registry.start(config.id)
                assert registry.wait_for_state(config.id, "running", timeout=15.0)
                wait_for_port("127.0.0.1", mcp_port, timeout=15.0)

                assert sorted(anyio.run(_mcp_list_tools, mcp_url)) == [
                    "thread_alpha",
                    "thread_beta",
                ]
                res_v1 = anyio.run(_mcp_call_tool, mcp_url, "thread_alpha", {})
                assert json.loads(res_v1["body"])["path"] == "/v1/thread-alpha"

                # 1. In-place edit (same id and name, updated URL and description)
                collection.requests[0] = RequestData(
                    id="req-1",
                    name="Thread Alpha",
                    method="GET",
                    url=f"http://127.0.0.1:{stub_port}/v2/thread-alpha-edited",
                    mcp_description="Thread Alpha v2 edited",
                    expose_as_mcp=True,
                )
                registry.refresh_collection(collection.id)

                wait_until(
                    lambda: "Thread Alpha v2 edited"
                    in anyio.run(_mcp_list_tool_details, mcp_url).get(
                        "thread_alpha", ""
                    ),
                    timeout=2.0,
                    description="thread-mode in-place tool description refresh",
                )
                res_v2 = anyio.run(_mcp_call_tool, mcp_url, "thread_alpha", {})
                assert (
                    json.loads(res_v2["body"])["path"]
                    == "/v2/thread-alpha-edited"
                )

                # 2. Add and remove tools
                collection.requests = [
                    collection.requests[0],
                    RequestData(
                        id="req-3",
                        name="Thread Gamma",
                        method="GET",
                        url=f"http://127.0.0.1:{stub_port}/v1/thread-gamma",
                        mcp_description="Thread Gamma v1",
                        expose_as_mcp=True,
                    ),
                ]
                registry.refresh_collection(collection.id)
                wait_for_port("127.0.0.1", mcp_port, timeout=15.0)

                wait_until(
                    lambda: sorted(anyio.run(_mcp_list_tools, mcp_url))
                    == ["thread_alpha", "thread_gamma"],
                    timeout=2.0,
                    description="thread-mode tool add/remove refresh",
                )
                res_gamma = anyio.run(_mcp_call_tool, mcp_url, "thread_gamma", {})
                assert json.loads(res_gamma["body"])["path"] == "/v1/thread-gamma"
            finally:
                registry.stop_all()
