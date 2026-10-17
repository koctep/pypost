"""Live wire IPC and stdio transport stress testing for standalone MCP servers.

Jira: PYPOST-1416
Architecture: ai-tasks/PYPOST-1416/20-architecture.md
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.request_service import ExecutionResult, ResponseData
from pypost.models.models import RequestData
from tests.helpers.port_allocation import allocate_tcp_port
from tests.helpers.qt_wait import wait_until
from tests.helpers.raw_tcp_client import RawTcpWireClient, parse_jsonrpc_from_response

pytestmark = pytest.mark.timeout(30)


def _create_mock_request_service():
    mock_svc = MagicMock()
    mock_svc.execute.side_effect = lambda req, vars, **kw: ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps({"result": vars.get("mcp", {}).get("request", {})}),
            elapsed_time=0.001,
            size=len(
                json.dumps({"result": vars.get("mcp", {}).get("request", {})}).encode("utf-8")
            ),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )
    return mock_svc


def test_tcp_wire_packet_fragmentation_streamable_http(qapp) -> None:
    """Spawns standalone MCP server, connects raw socket over loopback TCP,

    transmits complete handshake and tool call fragmented into arbitrary 1-byte/7-byte
    packet chunks, asserting valid framing and HTTP/JSON-RPC response.
    """
    port = allocate_tcp_port("127.0.0.1")
    tool = RequestData(
        id="wire_calc",
        name="wire_calc",
        method="POST",
        url="http://127.0.0.1/calc",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="127.0.0.1")

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")

        with RawTcpWireClient("127.0.0.1", port, timeout=10.0) as client:
            # 1. Initialize request fragmented into 7-byte chunks
            init_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "init-1",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "wire-tester", "version": "1.0"},
                    },
                }
            )
            client.send_fragmented(init_req, chunk_size=7)
            status, headers, body = client.read_http_response()
            assert status == 200
            assert client.session_id is not None
            msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == "init-1" for m in msgs)
            init_res = next(m for m in msgs if m.get("id") == "init-1")
            assert "capabilities" in init_res.get("result", {})

            # 2. Initialized notification fragmented into 7-byte chunks
            notif_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                }
            )
            client.send_fragmented(notif_req, chunk_size=7)
            status, headers, body = client.read_http_response()
            assert status == 202

            # 3. tools/list fragmented into 7-byte chunks
            list_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "list-1",
                    "method": "tools/list",
                    "params": {},
                }
            )
            client.send_fragmented(list_req, chunk_size=7)
            status, headers, body = client.read_http_response()
            assert status == 200
            msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == "list-1" for m in msgs)
            list_res = next(m for m in msgs if m.get("id") == "list-1")
            tools = list_res.get("result", {}).get("tools", [])
            assert any(t.get("name") == "wire_calc" for t in tools)

            # 4. tools/call fragmented into 1-byte micro chunks
            call_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "call-1",
                    "method": "tools/call",
                    "params": {
                        "name": "wire_calc",
                        "arguments": {"operand_a": 10, "operand_b": 20},
                    },
                }
            )
            client.send_fragmented(call_req, chunk_size=1)
            status, headers, body = client.read_http_response()
            assert status == 200
            msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == "call-1" for m in msgs)
            call_res = next(m for m in msgs if m.get("id") == "call-1")
            assert "content" in call_res.get("result", {})
            content = call_res["result"]["content"]
            assert len(content) > 0
            tool_payload = json.loads(content[0]["text"])
            assert tool_payload["status"] == 200
            assert tool_payload["error"] is False
            assert json.loads(tool_payload["body"]) == {
                "result": {"operand_a": 10, "operand_b": 20}
            }
    finally:
        manager.stop_server()


def test_tcp_wire_pipelined_burst_stress(qapp) -> None:
    """Rapid continuous burst of 50-100 tool execution requests over raw TCP wire

    asserting all responses match without resets or dropped packets.
    """
    port = allocate_tcp_port("127.0.0.1")
    tool = RequestData(
        id="burst_tool",
        name="burst_tool",
        method="POST",
        url="http://127.0.0.1/burst",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="127.0.0.1")

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")

        with RawTcpWireClient("127.0.0.1", port, timeout=15.0) as client:
            # Initialize session
            init_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "init-burst",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "wire-tester", "version": "1.0"},
                    },
                }
            )
            client.send_all(init_req)
            status, headers, body = client.read_http_response()
            assert status == 200
            assert client.session_id is not None

            notif_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                }
            )
            client.send_all(notif_req)
            status, headers, body = client.read_http_response()
            assert status == 202

            # Rapid pipelined burst of 100 tool execution requests
            burst_count = 100
            burst_bytes = b"".join(
                client.build_post_request(
                    {
                        "jsonrpc": "2.0",
                        "id": f"pipelined-{i}",
                        "method": "tools/call",
                        "params": {
                            "name": "burst_tool",
                            "arguments": {"seq": i, "payload": f"burst-val-{i}"},
                        },
                    }
                )
                for i in range(burst_count)
            )

            client.send_all(burst_bytes)

            received_ids = set()
            for _ in range(burst_count):
                status, headers, body = client.read_http_response()
                assert status == 200
                msgs = parse_jsonrpc_from_response(body)
                for m in msgs:
                    if "id" in m:
                        received_ids.add(m["id"])

            assert len(received_ids) == burst_count
            for i in range(burst_count):
                assert f"pipelined-{i}" in received_ids
    finally:
        manager.stop_server()


def test_stdio_subprocess_ipc_large_payload_and_burst() -> None:
    """Subprocess stdio pipe stress with concurrent non-blocking reader workers,

    50 request burst including large payloads (>64KB) asserting no OS pipe buffer
    deadlocks and clean exit on stdin close.
    """
    server_script = """
import asyncio
import json
import sys
from unittest.mock import MagicMock
from mcp.server.stdio import stdio_server
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.request_service import ExecutionResult, ResponseData
from pypost.models.models import RequestData

async def main():
    impl = MCPServerImpl(name="standalone-stdio-stress")
    tool = RequestData(
        id="stdio_echo",
        name="stdio_echo",
        method="POST",
        url="http://127.0.0.1/echo",
        expose_as_mcp=True,
    )
    mock_svc = MagicMock()
    def _execute(req, variables, **kw):
        payload = variables.get("mcp", {}).get("request", {}).get("payload", "")
        return ExecutionResult(
            response=ResponseData(
                status_code=200,
                headers={"content-type": "application/json"},
                body=json.dumps({"echo_payload": payload, "echo_length": len(payload)}),
                elapsed_time=0.001,
                size=len(payload),
            ),
            updated_variables={},
            script_logs=[],
            execution_error=None,
        )
    mock_svc.execute.side_effect = _execute
    impl._create_request_service = lambda: mock_svc
    impl.register_tools([tool])

    init_options = impl.server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await impl.server.run(read_stream, write_stream, init_options)

if __name__ == "__main__":
    asyncio.run(main())
"""

    process = subprocess.Popen(
        [sys.executable, "-c", server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )

    responses: dict[Any, dict[str, Any]] = {}
    response_lock = threading.Lock()
    stderr_output: list[str] = []

    def stdout_worker() -> None:
        assert process.stdout is not None
        for raw_line in iter(process.stdout.readline, b""):
            line = raw_line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
                with response_lock:
                    if "id" in msg:
                        responses[msg["id"]] = msg
            except Exception as e:
                stderr_output.append(f"stdout decode error: {e}")

    def stderr_worker() -> None:
        assert process.stderr is not None
        for raw_line in iter(process.stderr.readline, b""):
            stderr_output.append(raw_line.decode("utf-8", errors="replace"))

    t_out = threading.Thread(target=stdout_worker, daemon=True)
    t_err = threading.Thread(target=stderr_worker, daemon=True)
    t_out.start()
    t_err.start()

    try:
        assert process.stdin is not None

        # 1. Initialize handshake
        init_msg = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "stdio-tester", "version": "1.0"},
            },
        }
        process.stdin.write(json.dumps(init_msg).encode("utf-8") + b"\n")
        process.stdin.flush()

        deadline = time.time() + 5.0
        while time.time() < deadline:
            with response_lock:
                if 0 in responses:
                    break
            time.sleep(0.02)
        assert 0 in responses

        # 2. Initialized notification
        notif_msg = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        process.stdin.write(json.dumps(notif_msg).encode("utf-8") + b"\n")
        process.stdin.flush()

        # 3. Burst of 50 requests including large payloads (>64KB)
        total_requests = 50
        large_payload = "X" * 70000  # 70KB, exceeding 64KB OS pipe buffer
        for seq in range(1, total_requests + 1):
            payload = large_payload if seq > 40 else f"item-{seq}"
            req = {
                "jsonrpc": "2.0",
                "id": seq,
                "method": "tools/call",
                "params": {
                    "name": "stdio_echo",
                    "arguments": {"payload": payload},
                },
            }
            process.stdin.write(json.dumps(req).encode("utf-8") + b"\n")
        process.stdin.flush()

        # Wait for all 50 responses concurrently drained
        burst_deadline = time.time() + 15.0
        while time.time() < burst_deadline:
            with response_lock:
                if len(responses) >= total_requests + 1:
                    break
            time.sleep(0.05)

        with response_lock:
            for seq in range(1, total_requests + 1):
                assert seq in responses, f"Missing response for request id {seq}"
            # Verify large payload responses (>64KB) were not corrupted or truncated
            for seq in range(41, total_requests + 1):
                res = responses[seq]
                assert "result" in res
                content_text = res["result"]["content"][0]["text"]
                parsed = json.loads(content_text)
                assert parsed["status"] == 200
                assert parsed["error"] is False
                inner_body = json.loads(parsed["body"])
                assert inner_body["echo_length"] == 70000

        # 4. Clean exit on stdin close
        process.stdin.close()
        retcode = process.wait(timeout=5.0)
        assert retcode == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2.0)
        t_out.join(timeout=1.0)
        t_err.join(timeout=1.0)


def test_wire_lifecycle_teardown_and_port_rebind(qapp) -> None:
    """Rapid shutdown under active wire load and immediate socket re-binding

    verification without EADDRINUSE.
    """
    port = allocate_tcp_port("127.0.0.1")
    tool = RequestData(
        id="rebind_tool",
        name="rebind_tool",
        method="POST",
        url="http://127.0.0.1/rebind",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="127.0.0.1")

    stop_hammer = threading.Event()
    hammer_errors: list[Exception] = []

    def hammer_worker() -> None:
        while not stop_hammer.is_set():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    s.connect(("127.0.0.1", port))
                    s.sendall(
                        b"POST /mcp HTTP/1.1\r\n"
                        b"Host: 127.0.0.1\r\n"
                        b"Content-Type: application/json\r\n"
                        b"Accept: application/json, text/event-stream\r\n"
                        b"Content-Length: 2\r\n\r\n{}"
                    )
                    s.recv(1024)
            except OSError:
                pass
            except Exception as e:
                hammer_errors.append(e)

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")

        hammer_threads = [
            threading.Thread(target=hammer_worker, daemon=True)
            for _ in range(3)
        ]
        for t in hammer_threads:
            t.start()

        # Let traffic flow actively for 100ms
        time.sleep(0.1)

        # Rapid shutdown under active wire load
        stop_hammer.set()
        manager.stop_server()
        for t in hammer_threads:
            t.join(timeout=2.0)
        assert hammer_errors == []
        wait_until(lambda: not manager.is_running(), message="MCP server did not finish shutdown")

        # Verify socket re-binding without EADDRINUSE
        def can_bind() -> bool:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rebind_sock:
                    rebind_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    rebind_sock.bind(("127.0.0.1", port))
                    rebind_sock.listen(1)
                return True
            except OSError:
                return False

        wait_until(can_bind, timeout=5.0, message="Port failed to rebind without EADDRINUSE")

        # Verify new MCPServerManager can immediately bind and start on the exact same port
        manager2 = MCPServerManager()
        manager2._impl._create_request_service = lambda: mock_service
        manager2.start_server(port, [tool], host="127.0.0.1")
        try:
            wait_until(lambda: manager2.is_listening, message="New MCP server failed to bind")
            assert manager2.is_listening is True
        finally:
            manager2.stop_server()
    finally:
        stop_hammer.set()
        if manager.is_running():
            manager.stop_server()
