"""Loopback GitHub REST stand-in for the offline GitHub MCP wire test (PYPOST-1334).

The stub accepts every request, records its raw (still percent-encoded) path,
its parsed query, the ``Authorization``, ``Accept``, ``X-GitHub-Api-Version`` and
``Content-Type`` headers and the decoded JSON body, and answers ``200`` with a
small JSON document. Assertions live in the test, so a wrong path or query shows
up as a precise diff instead of a stub-side 404.
"""

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
_SERVER_THREAD_JOIN_TIMEOUT_SECONDS = 2.0
_MAX_BODY_BYTES = 64 * 1024


@dataclass(frozen=True)
class CapturedGitHubRequest:
    """Metadata captured from one loopback GitHub request."""

    method: str
    raw_path: str
    raw_query: str
    query: dict[str, list[str]]
    authorization: str | None
    accept: str | None
    api_version: str | None
    content_type: str | None
    body: Any = None


@dataclass(frozen=True)
class GitHubMcpCollectionHttpStub:
    """One running loopback stand-in and its request observation API."""

    base_url: str
    _captured_requests: list[CapturedGitHubRequest]

    @property
    def requests(self) -> tuple[CapturedGitHubRequest, ...]:
        """Return the captured requests in arrival order."""
        return tuple(self._captured_requests)


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


@contextmanager
def stub_github_mcp_collection_http() -> Iterator[GitHubMcpCollectionHttpStub]:
    """Run a capture-everything GitHub stand-in on a loopback ephemeral port."""
    captured_requests: list[CapturedGitHubRequest] = []
    capture_lock = threading.Lock()

    class _GitHubCollectionHandler(BaseHTTPRequestHandler):
        def _read_body(self) -> Any:
            length = min(int(self.headers.get("Content-Length", "0") or 0), _MAX_BODY_BYTES)
            raw_body = self.rfile.read(length) if length else b""
            if not raw_body:
                return None
            try:
                return json.loads(raw_body)
            except json.JSONDecodeError:
                return raw_body.decode("utf-8", errors="replace")

        def _capture_and_reply(self) -> None:
            parsed = urlsplit(self.path)
            captured = CapturedGitHubRequest(
                method=self.command,
                raw_path=parsed.path,
                raw_query=parsed.query,
                query=parse_qs(parsed.query, keep_blank_values=True),
                authorization=self.headers.get("Authorization"),
                accept=self.headers.get("Accept"),
                api_version=self.headers.get("X-GitHub-Api-Version"),
                content_type=self.headers.get("Content-Type"),
                body=self._read_body(),
            )
            with capture_lock:
                captured_requests.append(captured)
            content = _json_bytes({"id": 1, "offline": True})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        do_GET = _capture_and_reply
        do_POST = _capture_and_reply
        do_PUT = _capture_and_reply
        do_PATCH = _capture_and_reply
        do_DELETE = _capture_and_reply

        def log_message(self, _format: str, *_args: object) -> None:
            """Suppress expected loopback request logs during test execution."""

    httpd = ThreadingHTTPServer((_HOST, 0), _GitHubCollectionHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    stub = GitHubMcpCollectionHttpStub(f"http://{host}:{port}", captured_requests)
    try:
        yield stub
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=_SERVER_THREAD_JOIN_TIMEOUT_SECONDS)
        if thread.is_alive():
            raise RuntimeError("GitHub MCP collection loopback server did not stop")
