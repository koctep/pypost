"""Loopback Jira REST stand-in for the CI-safe MCP collection e2e test."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit


_HOST = "127.0.0.1"
_OFFLINE_ISSUE_KEY = "OFFLINE-1"
_SERVER_THREAD_JOIN_TIMEOUT_SECONDS = 2.0
_BOARD_QUERY = {
    "maxResults": ["1"],
    "startAt": ["0"],
    "projectKeyOrId": ["OFFLINE"],
}
_SEARCH_BODY = {
    "jql": "project = OFFLINE",
    "maxResults": 1,
    "fields": ["key"],
}


@dataclass(frozen=True)
class CapturedJiraRequest:
    """Safe metadata captured from one loopback Jira request."""

    method: str
    path: str
    query: dict[str, list[str]]
    body: dict[str, Any] | None = None


@dataclass(frozen=True)
class JiraMcpCollectionHttpStub:
    """One running loopback stand-in and its safe request observation API."""

    base_url: str
    _captured_requests: list[CapturedJiraRequest]

    @property
    def requests(self) -> tuple[CapturedJiraRequest, ...]:
        """Return test-local metadata for accepted canonical requests only."""
        return tuple(self._captured_requests)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


@contextmanager
def stub_jira_mcp_collection_http() -> Iterator[JiraMcpCollectionHttpStub]:
    """Run deterministic read-only Jira routes on a loopback ephemeral port."""
    captured_requests: list[CapturedJiraRequest] = []
    capture_lock = threading.Lock()

    class _JiraCollectionHandler(BaseHTTPRequestHandler):
        def _capture(
            self,
            path: str,
            query: dict[str, list[str]],
            body: dict[str, Any] | None = None,
        ) -> None:
            captured = CapturedJiraRequest(self.command, path, query, body)
            with capture_lock:
                captured_requests.append(captured)

        def _request_path_and_query(self) -> tuple[str, dict[str, list[str]]]:
            parsed = urlsplit(self.path)
            return parsed.path, parse_qs(parsed.query, keep_blank_values=True)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            content = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self) -> None:
            path, query = self._request_path_and_query()
            if path == "/rest/api/3/myself":
                if query:
                    self._send_json(400, {"error": "invalid query"})
                    return
                self._capture(path, {})
                self._send_json(
                    200,
                    {"accountId": "offline-account", "displayName": "Offline User"},
                )
                return
            if path == f"/rest/api/3/issue/{_OFFLINE_ISSUE_KEY}":
                if query:
                    self._send_json(400, {"error": "invalid query"})
                    return
                self._capture(path, {})
                self._send_json(200, {"key": _OFFLINE_ISSUE_KEY, "fields": {"summary": "Offline"}})
                return
            if path == "/rest/agile/1.0/board":
                if query != _BOARD_QUERY:
                    self._send_json(400, {"error": "invalid board query"})
                    return
                self._capture(path, _BOARD_QUERY)
                self._send_json(
                    200,
                    {
                        "maxResults": 1,
                        "startAt": 0,
                        "values": [{"id": 1, "name": "Offline"}],
                    },
                )
                return
            self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:
            path, query = self._request_path_and_query()
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)
            try:
                body = json.loads(raw_body) if raw_body else None
            except json.JSONDecodeError:
                body = None
            if path != "/rest/api/3/search/jql":
                self._send_json(404, {"error": "not found"})
                return
            if query or body != _SEARCH_BODY:
                self._send_json(400, {"error": "invalid search request"})
                return
            self._capture(path, {}, _SEARCH_BODY)
            self._send_json(200, {"issues": [{"key": _OFFLINE_ISSUE_KEY}]})

        def _method_not_allowed(self) -> None:
            self._send_json(405, {"error": "method not allowed"})

        do_DELETE = _method_not_allowed
        do_PATCH = _method_not_allowed
        do_PUT = _method_not_allowed

        def log_message(self, _format: str, *_args: object) -> None:
            """Suppress expected loopback request logs during test execution."""

    httpd = ThreadingHTTPServer((_HOST, 0), _JiraCollectionHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    stub = JiraMcpCollectionHttpStub(f"http://{host}:{port}", captured_requests)
    try:
        yield stub
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=_SERVER_THREAD_JOIN_TIMEOUT_SECONDS)
        if thread.is_alive():
            raise RuntimeError("Jira MCP collection loopback server did not stop")
