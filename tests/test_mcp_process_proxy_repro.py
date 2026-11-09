"""Process proxy forwarding acceptance regressions for PYPOST-1464."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from typing import Any, Iterator

import anyio
import pytest

from pypost.core.mcp_process_supervisor import McpProcessSupervisor
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.mcp_server_runner import ProcessServerRunner, ServerStartSpec
from pypost.models.models import Environment, RequestData
from pypost.models.settings import McpServerConfiguration
from tests.helpers.mcp_live_server import LiveMCPServer
from tests.helpers.port_allocation import EphemeralPortReserve
from tests.test_mcp_server_integration import _exec_result, _mcp_call_tool, _mcp_list_tools

pytestmark = pytest.mark.timeout(60)


@contextmanager
def _upstream(name: str) -> Iterator[tuple[LiveMCPServer, list[dict[bytes, bytes]]]]:
    tool = RequestData(
        id=name, name=name, method="GET", url="http://unused.invalid", expose_as_mcp=True
    )
    server = LiveMCPServer([tool], execute_result=_exec_result(name))
    headers: list[dict[bytes, bytes]] = []
    create_app = server.impl.create_app

    def instrumented_app() -> Any:
        app = create_app()

        async def capture(scope: dict, receive: Any, send: Any) -> None:
            if scope["type"] == "http":
                headers.append(dict(scope["headers"]))
            await app(scope, receive, send)

        return capture

    server.impl.create_app = instrumented_app
    server.start()
    try:
        assert anyio.run(_mcp_list_tools, server.mcp_url) == [name]
        assert anyio.run(_mcp_call_tool, server.mcp_url, name)["body"] == name
        headers.clear()
        yield server, headers
    finally:
        server.stop()


def _config(
    port: int, upstream_url: str, transport: str = "streamable_http"
) -> McpServerConfiguration:
    return McpServerConfiguration(
        id="process-proxy",
        name="Isolated proxy",
        port=port,
        server_type="proxy",
        upstream_url=upstream_url,
        upstream_transport=transport,
        headers={"Authorization": "Bearer {{ TOKEN }}"},
        timeout=7.5,
    )


@pytest.mark.parametrize("transport", ["streamable_http", "sse"])
def test_process_proxy_forwards_upstream_tools_and_resolved_headers(
    transport: str, caplog: pytest.LogCaptureFixture
) -> None:
    reserve = EphemeralPortReserve(1)
    port = reserve.allocate()[0]
    supervisor = McpProcessSupervisor()
    runner = ProcessServerRunner("proxy-wire", supervisor)
    try:
        with _upstream("upstream_only") as (upstream, received):
            path = "/mcp" if transport == "streamable_http" else "/sse/"
            upstream_url = f"http://127.0.0.1:{upstream.port}{path}"
            config = _config(port, upstream_url, transport)
            caplog.clear()
            with caplog.at_level(logging.INFO, logger="pypost.core.mcp_process_supervisor"):
                reserve.release()
                runner.start(
                    ServerStartSpec(configuration=config, variables={"TOKEN": "owned-token"})
                )
                url = f"http://127.0.0.1:{port}/mcp"
                assert anyio.run(_mcp_list_tools, url) == ["upstream_only"]
                result = anyio.run(_mcp_call_tool, url, "upstream_only")
            assert result["body"] == "upstream_only"
            assert received
            assert all(h.get(b"authorization") == b"Bearer owned-token" for h in received)
            assert any("mcp_worker_spawned instance_id=proxy-wire " in m for m in caplog.messages)
            assert any("mcp_worker_started instance_id=proxy-wire " in m for m in caplog.messages)
            assert "owned-token" not in caplog.text
            assert upstream_url not in caplog.text
    finally:
        runner.stop()
        supervisor.shutdown()
        assert reserve.verify_all_rebound(timeout=5)


def test_process_start_payload_preserves_proxy_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    reserve = EphemeralPortReserve(1)
    port = reserve.allocate()[0]
    supervisor = McpProcessSupervisor()
    runner = ProcessServerRunner("proxy-payload", supervisor)
    sent: list[dict] = []
    original_send = supervisor._send

    def capture(instance_id: str, message: dict) -> None:
        if message.get("type") == "START":
            sent.append(message)
        original_send(instance_id, message)

    monkeypatch.setattr(supervisor, "_send", capture)
    config = _config(port, "http://127.0.0.1:9/custom/sse", "sse")
    try:
        reserve.release()
        runner.start(ServerStartSpec(configuration=config, variables={"TOKEN": "payload-token"}))
        assert len(sent) == 1
        start = sent[0]
        assert start.get("server_type") == "proxy"
        assert start.get("upstream_url") == config.upstream_url
        assert start.get("upstream_transport") == "sse"
        assert start.get("headers") == config.headers
        assert start.get("timeout") == 7.5
        config.headers["Authorization"] = "changed-after-start"
        assert start["headers"]["Authorization"] == "Bearer {{ TOKEN }}"
    finally:
        runner.stop()
        supervisor.shutdown()
        assert reserve.verify_all_rebound(timeout=5)


def test_registry_process_proxy_reconfigure_changes_upstream(
    caplog: pytest.LogCaptureFixture,
) -> None:
    reserve = EphemeralPortReserve(2)
    ports = reserve.allocate()
    environment = Environment(id="proxy-env", name="Proxy", variables={"TOKEN": "registry-token"})
    registry = MCPServerRegistry(
        execution_mode="process", environment_lookup=lambda _id: environment
    )
    try:
        with _upstream("first_upstream") as (first, _):
            with _upstream("second_upstream") as (second, received):
                config = _config(ports[0], first.mcp_url).model_copy(
                    update={"environment_id": environment.id}
                )
                registry.upsert(config)
                caplog.clear()
                with caplog.at_level(logging.INFO, logger="pypost.core.mcp_server_registry"):
                    reserve.release()
                    registry.start(config.id)
                    assert anyio.run(_mcp_list_tools, f"http://127.0.0.1:{ports[0]}/mcp") == [
                        "first_upstream"
                    ]
                    replacement = config.model_copy(
                        update={"port": ports[1], "upstream_url": second.mcp_url}, deep=True
                    )
                    registry.reconfigure(config.id, replacement)
                assert registry.configuration(config.id) == replacement
                assert anyio.run(_mcp_list_tools, f"http://127.0.0.1:{ports[1]}/mcp") == [
                    "second_upstream"
                ]
                assert received
                assert all(h.get(b"authorization") == b"Bearer registry-token" for h in received)
                assert (
                    f"mcp_registry_process_reconfigured instance_id={config.id}"
                    in caplog.messages
                )
                assert "registry-token" not in caplog.text
                assert first.mcp_url not in caplog.text
                assert second.mcp_url not in caplog.text
    finally:
        registry.stop_all()
        assert reserve.verify_all_rebound(timeout=5)
