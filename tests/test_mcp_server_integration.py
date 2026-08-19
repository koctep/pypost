"""Integration tests: live MCP server over Streamable HTTP round-trip (PYPOST-368/551)."""
import pytest

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlsplit

import anyio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from pypost.core.mcp_client_service import MCPClientService
from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.request_service import ExecutionResult
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from tests.helpers.mcp_live_server import (
    LiveMCPServer,
    free_port,
    live_mcp_server,
    wait_for_port,
)


pytestmark = pytest.mark.timeout(120)


_REPO_ROOT = Path(__file__).resolve().parents[1]
_JIRA_MCP_COLLECTION_PATH = _REPO_ROOT / "examples" / "collections" / "jira_mcp.json"

_JIRA_NUMERIC_PATH_CASES = (
    (
        "jira-list-board-sprints",
        "jira_list_board_sprints",
        "board_id",
        "/rest/agile/1.0/board/42/sprint",
        {"state": "active", "maxResults": 50, "startAt": 0},
    ),
    ("jira-get-sprint", "jira_get_sprint", "sprint_id", "/rest/agile/1.0/sprint/42", {}),
    (
        "jira-update-sprint",
        "jira_update_sprint",
        "sprint_id",
        "/rest/agile/1.0/sprint/42",
        {"sprint_payload": '{"name":"Renamed"}'},
    ),
    ("jira-delete-sprint", "jira_delete_sprint", "sprint_id", "/rest/agile/1.0/sprint/42", {}),
    (
        "jira-add-issues-to-sprint",
        "jira_add_issues_to_sprint",
        "sprint_id",
        "/rest/agile/1.0/sprint/42/issue",
        {"issues_payload": '{"issues":["DEMO-1"]}'},
    ),
    (
        "jira-get-sprint-issues",
        "jira_get_sprint_issues",
        "sprint_id",
        "/rest/agile/1.0/sprint/42/issue",
        {"maxResults": 50, "startAt": 0},
    ),
)


def _jira_mcp_request_with_local_url(request_id: str, url: str) -> RequestData:
    """Import one shipped Jira MCP request and isolate only its destination."""
    collections, parse_errors = load_collection_import_candidates(_JIRA_MCP_COLLECTION_PATH)
    assert parse_errors == []
    assert len(collections) == 1
    request = next(request for request in collections[0].requests if request.id == request_id)
    return request.model_copy(update={"url": url}, deep=True)


def _jira_mcp_request_with_local_base_url(request_id: str, base_url: str) -> RequestData:
    """Import one shipped Jira request while preserving its path template."""
    collections, parse_errors = load_collection_import_candidates(_JIRA_MCP_COLLECTION_PATH)
    assert parse_errors == []
    assert len(collections) == 1
    request = next(request for request in collections[0].requests if request.id == request_id)
    return request.model_copy(
        update={"url": request.url.replace("{{ jira_base_url }}", base_url)}, deep=True
    )


def _exec_result(body: str = "ok") -> ExecutionResult:
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


async def _mcp_list_tools(mcp_url: str) -> list[str]:
    async with create_mcp_http_client() as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]


async def _mcp_call_tool(mcp_url: str, name: str, arguments: dict | None = None) -> dict:
    result = await _mcp_call_tool_result(mcp_url, name, arguments)
    return json.loads(result.content[0].text)


async def _mcp_call_tool_result(mcp_url: str, name: str, arguments: dict | None = None):
    async with create_mcp_http_client() as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(name, arguments or {})


class TestMCPServerIntegration(unittest.TestCase):
    def test_jira_numeric_path_identifiers_accept_decimal_strings_and_native_integers(self):
        """PYPOST-1038 R4: every published numeric path accepts both forms end-to-end."""
        for (
            request_id,
            tool_name,
            identifier_name,
            path_fragment,
            extra_arguments,
        ) in _JIRA_NUMERIC_PATH_CASES:
            for identifier_value in ("42", 42):
                with self.subTest(request_id=request_id, identifier_value=identifier_value):
                    stub_port = free_port()
                    captured_paths: list[str] = []

                    class _StubHandler(BaseHTTPRequestHandler):
                        def _respond(self):
                            captured_paths.append(self.path)
                            payload = b"{}"
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(payload)))
                            self.end_headers()
                            self.wfile.write(payload)

                        do_GET = _respond
                        do_POST = _respond
                        do_PUT = _respond
                        do_DELETE = _respond

                        def log_message(self, _format, *_args):
                            return

                    httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
                    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                    server_thread.start()
                    try:
                        tool = _jira_mcp_request_with_local_base_url(
                            request_id,
                            f"http://127.0.0.1:{stub_port}",
                        )
                        arguments = {identifier_name: identifier_value, **extra_arguments}
                        with live_mcp_server([tool]) as mcp_server:
                            mcp_server.impl.set_variable_supplier(
                                lambda: {"jira_credentials": "user:token"}
                            )
                            result = anyio.run(
                                _mcp_call_tool_result,
                                mcp_server.mcp_url,
                                tool_name,
                                arguments,
                            )
                        self.assertFalse(result.isError)
                        payload = json.loads(result.content[0].text)
                        self.assertFalse(payload["error"])
                        self.assertEqual(payload["status"], 200)
                        self.assertEqual(
                            [urlsplit(path).path for path in captured_paths], [path_fragment]
                        )
                    finally:
                        httpd.shutdown()
                        server_thread.join(timeout=2.0)

    def test_jira_non_integral_identifier_never_dispatches_to_http(self):
        """PYPOST-1038 R5: to_int fails closed before HTTP dispatch."""
        for request_id, tool_name, identifier_name, path_fragment, extra_arguments in (
            _JIRA_NUMERIC_PATH_CASES[0],
            _JIRA_NUMERIC_PATH_CASES[1],
        ):
            for identifier_value in ("not-an-id", 42.0):
                with self.subTest(request_id=request_id, identifier_value=identifier_value):
                    stub_port = free_port()
                    captured_paths: list[str] = []

                    class _StubHandler(BaseHTTPRequestHandler):
                        def do_GET(self):
                            captured_paths.append(self.path)
                            self.send_response(200)
                            self.end_headers()

                        def log_message(self, _format, *_args):
                            return

                    httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
                    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                    server_thread.start()
                    try:
                        tool = _jira_mcp_request_with_local_base_url(
                            request_id,
                            f"http://127.0.0.1:{stub_port}",
                        )
                        arguments = {identifier_name: identifier_value, **extra_arguments}
                        with live_mcp_server([tool]) as mcp_server:
                            mcp_server.impl.set_variable_supplier(
                                lambda: {"jira_credentials": "user:token"}
                            )
                            result = anyio.run(
                                _mcp_call_tool_result,
                                mcp_server.mcp_url,
                                tool_name,
                                arguments,
                            )
                        if identifier_value == "not-an-id":
                            self.assertTrue(result.isError)
                        else:
                            payload = json.loads(result.content[0].text)
                            self.assertTrue(payload["error"])
                            self.assertEqual(payload["error_category"], "template")
                        self.assertEqual(captured_paths, [])
                    finally:
                        httpd.shutdown()
                        server_thread.join(timeout=2.0)

    def test_mcp_client_service_list_tools_over_live_streamable_http(self):
        """MCPClientService sync wrapper works against live server (PYPOST-560)."""
        tool = RequestData(
            name="Echo Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.msg }}",
        )
        with live_mcp_server([tool]) as server:
            service = MCPClientService()
            result = service.run(server.mcp_url, "list_tools", None)

        self.assertEqual(result.status_code, 200)
        body = json.loads(result.body)
        self.assertEqual([t["name"] for t in body["tools"]], ["echo_tool"])

    def test_list_tools_over_live_streamable_http(self):
        tool = RequestData(
            name="Echo Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.msg }}",
        )
        with live_mcp_server([tool]) as server:
            names = anyio.run(_mcp_list_tools, server.mcp_url)
            self.assertEqual(names, ["echo_tool"])

    def test_call_tool_over_live_streamable_http_returns_response_body(self):
        tool = RequestData(
            name="Ping",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/ping",
        )
        with live_mcp_server([tool], execute_result=_exec_result("pong")) as server:
            payload = anyio.run(_mcp_call_tool, server.mcp_url, "ping", {})
            self.assertFalse(payload["error"])
            self.assertEqual(payload["status"], 200)
            self.assertEqual(payload["body"], "pong")

    def test_call_tool_passes_mcp_arguments_to_request_service(self):
        tool = RequestData(
            name="Greet",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.name }}",
        )
        with live_mcp_server([tool], execute_result=_exec_result("hello")) as server:
            anyio.run(_mcp_call_tool, server.mcp_url, "greet", {"name": "world"})
            server._mock_request_service.execute.assert_called_once()
            _req, ctx = server._mock_request_service.execute.call_args[0]
            self.assertEqual(ctx, {"mcp": {"request": {"name": "world"}}})

    def test_call_tool_passes_env_and_mcp_variables_to_request_service(self):
        tool = RequestData(
            name="Fetch",
            expose_as_mcp=True,
            method="GET",
            url="{{ base_url }}/{{ mcp.request.id }}",
        )
        server = LiveMCPServer([tool], execute_result=_exec_result("ok"))
        server.impl.set_variable_supplier(lambda: {"base_url": "http://api"})
        server.start()
        try:
            anyio.run(_mcp_call_tool, server.mcp_url, "fetch", {"id": "1"})
            _req, ctx = server._mock_request_service.execute.call_args[0]
            self.assertEqual(
                ctx,
                {
                    "base_url": "http://api",
                    "mcp": {"request": {"id": "1"}},
                },
            )
        finally:
            server.stop()

    def test_call_tool_executes_real_outbound_http_via_stub(self):
        """MCP tool call hits a local HTTP stub (PYPOST-564), not mocked execute."""
        stub_port = free_port()
        stub_body = "stub-response"

        class _StubHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                payload = stub_body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        try:
            tool = RequestData(
                name="Stub Echo",
                expose_as_mcp=True,
                method="GET",
                url=f"http://127.0.0.1:{stub_port}/echo",
            )
            with live_mcp_server([tool]) as mcp_server:
                payload = anyio.run(_mcp_call_tool, mcp_server.mcp_url, "stub_echo", {})
            self.assertFalse(payload["error"])
            self.assertEqual(payload["status"], 200)
            self.assertEqual(payload["body"], stub_body)
        finally:
            httpd.shutdown()
            server_thread.join(timeout=2.0)

    def test_call_tool_substitutes_mcp_request_path_placeholder(self):
        """PYPOST-1033: call_tool must not leave literal {{ mcp.request... }}."""
        stub_port = free_port()
        captured_paths: list[str] = []

        class _StubHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                captured_paths.append(self.path)
                payload = b"ok"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        try:
            tool = RequestData(
                name="Get Issue",
                expose_as_mcp=True,
                method="GET",
                url=(
                    f"http://127.0.0.1:{stub_port}/issue/"
                    "{{ mcp.request.issue_key }}"
                ),
            )
            with live_mcp_server([tool]) as mcp_server:
                payload = anyio.run(
                    _mcp_call_tool,
                    mcp_server.mcp_url,
                    "get_issue",
                    {"issue_key": "PROJ-1"},
                )
            self.assertFalse(payload["error"])
            self.assertEqual(payload["status"], 200)
            self.assertEqual(1, len(captured_paths))
            path = captured_paths[0]
            self.assertEqual("/issue/PROJ-1", path)
            self.assertNotIn("mcp.request", path)
            self.assertNotIn("%7B%7B", path)
        finally:
            httpd.shutdown()
            server_thread.join(timeout=2.0)

    def test_call_tool_substitutes_jira_mcp_query_parameter(self):
        """PYPOST-1034: Jira MCP query placeholders reach the wire rendered."""
        stub_port = free_port()
        captured_paths: list[str] = []

        class _StubHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                captured_paths.append(self.path)
                payload = b"{}"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        try:
            tool = _jira_mcp_request_with_local_url(
                "jira-search-fields",
                f"http://127.0.0.1:{stub_port}/rest/api/3/field/search",
            )
            with live_mcp_server([tool]) as mcp_server:
                mcp_server.impl.set_variable_supplier(
                    lambda: {"jira_credentials": "user:token"}
                )
                payload = anyio.run(
                    _mcp_call_tool,
                    mcp_server.mcp_url,
                    "jira_search_fields",
                    {"query": "Story Point"},
                )
            self.assertFalse(payload["error"])
            self.assertEqual(payload["status"], 200)
            self.assertEqual(len(captured_paths), 1)
            path = captured_paths[0]
            self.assertEqual(parse_qs(urlsplit(path).query), {"query": ["Story Point"]})
            self.assertNotIn("mcp.request", path)
            self.assertNotIn("%7B", path)
        finally:
            httpd.shutdown()
            server_thread.join(timeout=2.0)

    def test_jira_list_boards_omits_project_key_when_unset_and_includes_when_set(self):
        """PYPOST-1068: jira-list-boards must omit projectKeyOrId when unset, include when set."""
        for env_dict, expected_project_in_query in (
            ({"jira_credentials": "user:token"}, False),
            ({"jira_credentials": "user:token", "jira_project_key": ""}, False),
            ({"jira_credentials": "user:token", "jira_project_key": "PROJ"}, True),
        ):
            with self.subTest(
                env_dict=env_dict,
                expected_project_in_query=expected_project_in_query,
            ):
                stub_port = free_port()
                captured_paths: list[str] = []

                class _StubHandler(BaseHTTPRequestHandler):
                    def do_GET(self):
                        captured_paths.append(self.path)
                        payload = b'{"values": []}'
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(payload)))
                        self.end_headers()
                        self.wfile.write(payload)

                    def log_message(self, _format, *_args):
                        return

                httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
                server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                server_thread.start()
                try:
                    tool = _jira_mcp_request_with_local_url(
                        "jira-list-boards",
                        f"http://127.0.0.1:{stub_port}/rest/agile/1.0/board",
                    )
                    with live_mcp_server([tool]) as mcp_server:
                        mcp_server.impl.set_variable_supplier(lambda: env_dict)
                        payload = anyio.run(
                            _mcp_call_tool,
                            mcp_server.mcp_url,
                            "jira_list_boards",
                            {"maxResults": 50, "startAt": 0},
                        )
                    self.assertFalse(payload["error"])
                    self.assertEqual(payload["status"], 200)
                    self.assertEqual(len(captured_paths), 1)
                    query = parse_qs(urlsplit(captured_paths[0]).query)
                    self.assertEqual(query.get("maxResults"), ["50"])
                    self.assertEqual(query.get("startAt"), ["0"])
                    if expected_project_in_query:
                        self.assertEqual(query.get("projectKeyOrId"), ["PROJ"])
                    else:
                        self.assertNotIn("projectKeyOrId", query)
                finally:
                    httpd.shutdown()
                    server_thread.join(timeout=2.0)

    def test_call_tool_substitutes_jira_mcp_json_body(self):
        """PYPOST-1034: Jira MCP JSON-body placeholders reach the wire rendered."""
        stub_port = free_port()
        captured_bodies: list[bytes] = []

        class _StubHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                captured_bodies.append(self.rfile.read(length))
                payload = b'{"issues": []}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        try:
            tool = _jira_mcp_request_with_local_url(
                "jira-search-issues-jql",
                f"http://127.0.0.1:{stub_port}/rest/api/3/search/jql",
            )
            search_payload = {"jql": "project = DEMO", "maxResults": 1}
            with live_mcp_server([tool]) as mcp_server:
                mcp_server.impl.set_variable_supplier(
                    lambda: {"jira_credentials": "user:token"}
                )
                payload = anyio.run(
                    _mcp_call_tool,
                    mcp_server.mcp_url,
                    "jira_search_issues_jql",
                    {"search_payload": json.dumps(search_payload)},
                )
            self.assertFalse(payload["error"])
            self.assertEqual(payload["status"], 200)
            self.assertEqual(len(captured_bodies), 1)
            body = captured_bodies[0].decode("utf-8")
            self.assertEqual(json.loads(body), search_payload)
            self.assertNotIn("mcp.request", body)
            self.assertNotIn("{{", body)
        finally:
            httpd.shutdown()
            server_thread.join(timeout=2.0)


class TestMCPServerManagerIntegration(unittest.TestCase):
    """Exercise production MCPServerManager thread + uvicorn lifecycle."""

    def test_manager_starts_server_and_invokes_tool(self):
        port = free_port()
        tool = RequestData(
            name="Mgr Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/m",
        )
        manager = MCPServerManager()
        mock_svc = MagicMock()
        mock_svc.execute.return_value = _exec_result("from-manager")
        manager._impl._create_request_service = lambda: mock_svc
        manager.start_server(port, [tool], host="127.0.0.1")
        try:
            wait_for_port("127.0.0.1", port)
            mcp_url = f"http://127.0.0.1:{port}/mcp"
            payload = anyio.run(_mcp_call_tool, mcp_url, "mgr_tool", {})
            self.assertEqual(payload["body"], "from-manager")
            self.assertFalse(payload["error"])
            self.assertTrue(manager.is_running())
        finally:
            manager.stop_server()
            self.assertFalse(manager.is_running())


if __name__ == "__main__":
    unittest.main()
