"""PYPOST-1454: Real Remote HTTP Transport Abort and Session Teardown Repro Suite.

Desired behavior:
1. When an in-flight HTTP request is blocked waiting on remote server I/O, triggering
   cancellation on the associated CancellationToken must immediately sever the active
   HTTP session / underlying socket, aborting the request in < 0.5s.
2. The transport layer must translate the abort into OperationCancelledError instead of
   presenting generic socket/network failures or hanging until socket timeout.
3. If CancellationToken is already cancelled before dispatch, send_request must raise
   OperationCancelledError immediately with zero network overhead.
4. Transport abort callbacks registered on CancellationToken must be cleaned up in
   finally blocks upon request completion (normal or error) to prevent callback leaks.
5. After a transport abort severs a session, subsequent requests executed on the same
   client instance must succeed without being broken by the closed connection pool.

Before Step 4:
- HTTPClient.send_request does not accept or register cancellation_token callbacks.
- In-flight requests cannot be unblocked by CancellationToken and remain blocked.
- OperationCancelledError is not raised.
"""
from __future__ import annotations

import http.server
import inspect
import logging
import threading
import time
from typing import Any, Generator

import pytest

from pypost.core.cancellation import (
    CancellationTokenSource,
    OperationCancelledError,
    call_with_cancellation_token,
)
from pypost.core.http_client import HTTPClient
from pypost.models.models import RequestData

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.timeout(30)

BLOCK_BUDGET_S = 3.0
ABORT_ELAPSED_LIMIT_S = 0.5


class _StallServerHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for local ephemeral loopback tests."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy stderr logging during automated tests."""
        pass

    def do_GET(self) -> None:
        server = getattr(self.server, "test_context", None)
        if self.path == "/slow":
            if server is not None:
                server.request_received.set()
                # Stalls response until test finishes or stop_event is signaled
                server.stop_event.wait(timeout=BLOCK_BUDGET_S)
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", "4")
                self.end_headers()
                self.wfile.write(b"slow")
            except (BrokenPipeError, ConnectionResetError, OSError):
                # Expected when client severs connection during transport abort
                pass
        elif self.path == "/fast":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()


class _StallServer(http.server.ThreadingHTTPServer):
    """Threading HTTPServer tracking request state for abort testing."""

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _StallServerHandler)
        self.daemon_threads = True
        self.request_received = threading.Event()
        self.stop_event = threading.Event()
        self.test_context = self


@pytest.fixture
def stall_server() -> Generator[tuple[_StallServer, str], None, None]:
    """Start an ephemeral loopback HTTP server and tear down cleanly."""
    server = _StallServer()
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = server.server_port
    base_url = f"http://127.0.0.1:{port}"

    try:
        yield server, base_url
    finally:
        server.stop_event.set()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2.0)


@pytest.mark.timeout(30)
def test_http_client_in_flight_request_aborts_promptly_on_cancellation(
    stall_server: tuple[_StallServer, str],
) -> None:
    """Triggering cancellation mid-flight must abort socket and raise OperationCancelledError."""
    server, base_url = stall_server
    client = HTTPClient()
    cts = CancellationTokenSource()
    request_data = RequestData(method="GET", url=f"{base_url}/slow")

    worker_result: dict[str, Any] = {"result": None, "error": None}

    def worker_target() -> None:
        try:
            worker_result["result"] = call_with_cancellation_token(
                client.send_request,
                request_data,
                cancellation_token=cts.token,
            )
        except Exception as exc:
            worker_result["error"] = exc

    worker_thread = threading.Thread(target=worker_target, daemon=True)
    worker_thread.start()

    # Ensure the HTTP connection is established and server enters stall state
    assert server.request_received.wait(timeout=2.0), "Server did not receive request in time"

    # Trigger cancellation mid-flight while blocked on socket
    t0 = time.monotonic()
    cts.cancel(reason="test in-flight transport abort")

    # In-flight request must abort promptly (< 0.5s), well before BLOCK_BUDGET_S (3.0s)
    worker_thread.join(timeout=ABORT_ELAPSED_LIMIT_S)
    elapsed = time.monotonic() - t0

    try:
        assert not worker_thread.is_alive(), (
            f"In-flight HTTP request must abort promptly (< {ABORT_ELAPSED_LIMIT_S}s) on "
            f"cancellation; worker thread is still blocked (elapsed={elapsed:.3f}s, "
            f"budget={BLOCK_BUDGET_S}s)"
        )
        assert isinstance(worker_result["error"], OperationCancelledError), (
            f"Cancelled HTTP request must raise OperationCancelledError, got "
            f"{worker_result['error']!r}"
        )
    finally:
        server.stop_event.set()
        worker_thread.join(timeout=1.0)


@pytest.mark.timeout(30)
def test_http_client_send_request_accepts_cancellation_token_parameter(
    stall_server: tuple[_StallServer, str],
) -> None:
    """HTTPClient.send_request must directly accept cancellation_token keyword argument."""
    server, base_url = stall_server
    client = HTTPClient()
    cts = CancellationTokenSource()
    request_data = RequestData(method="GET", url=f"{base_url}/fast")

    # In Step 4, send_request must directly accept cancellation_token
    sig = inspect.signature(client.send_request)
    assert "cancellation_token" in sig.parameters, (
        "HTTPClient.send_request must declare cancellation_token parameter"
    )

    result = client.send_request(request_data, cancellation_token=cts.token)
    assert result.response.status_code == 200


@pytest.mark.timeout(30)
def test_pre_cancelled_token_aborts_before_network_dispatch(
    stall_server: tuple[_StallServer, str],
) -> None:
    """Pre-cancelled token must immediately raise OperationCancelledError."""
    server, base_url = stall_server
    client = HTTPClient()
    cts = CancellationTokenSource()
    cts.cancel(reason="pre-cancelled token")
    request_data = RequestData(method="GET", url=f"{base_url}/slow")

    # Pre-cancelled token must immediately raise OperationCancelledError
    with pytest.raises(OperationCancelledError):
        call_with_cancellation_token(
            client.send_request,
            request_data,
            cancellation_token=cts.token,
        )

    # Outbound network connection must NOT have been initiated
    assert not server.request_received.is_set(), (
        "Pre-cancelled token must abort before initiating outbound HTTP connection"
    )


@pytest.mark.timeout(30)
def test_cancellation_callback_unregistered_after_request_completion(
    stall_server: tuple[_StallServer, str],
) -> None:
    """Cancellation abort callback must be unregistered in finally block to prevent leaks."""
    server, base_url = stall_server
    client = HTTPClient()
    cts = CancellationTokenSource()
    request_data = RequestData(method="GET", url=f"{base_url}/fast")

    sig = inspect.signature(client.send_request)
    assert "cancellation_token" in sig.parameters, (
        "HTTPClient.send_request must declare cancellation_token parameter"
    )

    assert len(cts._callbacks) == 0
    result = client.send_request(request_data, cancellation_token=cts.token)
    assert result.response.status_code == 200
    assert len(cts._callbacks) == 0, (
        "Transport abort callback must be unregistered upon request completion"
    )


@pytest.mark.timeout(30)
def test_subsequent_request_succeeds_after_transport_abort(
    stall_server: tuple[_StallServer, str],
) -> None:
    """Client instance must recover and execute subsequent requests cleanly after an abort."""
    server, base_url = stall_server
    client = HTTPClient()
    cts = CancellationTokenSource()
    slow_request = RequestData(method="GET", url=f"{base_url}/slow")
    fast_request = RequestData(method="GET", url=f"{base_url}/fast")

    worker_result: dict[str, Any] = {"error": None}

    def worker_target() -> None:
        try:
            call_with_cancellation_token(
                client.send_request,
                slow_request,
                cancellation_token=cts.token,
            )
        except Exception as exc:
            worker_result["error"] = exc

    worker_thread = threading.Thread(target=worker_target, daemon=True)
    worker_thread.start()

    assert server.request_received.wait(timeout=2.0)
    cts.cancel(reason="test abort recovery")
    worker_thread.join(timeout=ABORT_ELAPSED_LIMIT_S)

    try:
        assert not worker_thread.is_alive(), "Worker thread must abort promptly"
        assert isinstance(worker_result["error"], OperationCancelledError)
        # Subsequent request on the same client instance must succeed
        res = client.send_request(fast_request)
        assert res.response.status_code == 200
    finally:
        server.stop_event.set()
        worker_thread.join(timeout=1.0)


@pytest.mark.timeout(30)
def test_transport_abort_emits_structured_logs(
    stall_server: tuple[_StallServer, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Transport abort lifecycle must emit structured logs without spurious errors."""
    server, base_url = stall_server
    client = HTTPClient()
    cts = CancellationTokenSource()
    slow_request = RequestData(method="GET", url=f"{base_url}/slow")

    worker_result: dict[str, Any] = {"error": None}

    def worker_target() -> None:
        try:
            with caplog.at_level(logging.DEBUG):
                call_with_cancellation_token(
                    client.send_request,
                    slow_request,
                    cancellation_token=cts.token,
                )
        except Exception as exc:
            worker_result["error"] = exc

    worker_thread = threading.Thread(target=worker_target, daemon=True)
    worker_thread.start()

    assert server.request_received.wait(timeout=2.0)
    cts.cancel(reason="test abort logging")
    worker_thread.join(timeout=ABORT_ELAPSED_LIMIT_S)

    try:
        assert not worker_thread.is_alive()
        assert isinstance(worker_result["error"], OperationCancelledError)

        messages = [record.getMessage() for record in caplog.records]
        # Verify structured lifecycle events were logged
        assert any("http_transport_abort_triggered" in m for m in messages), (
            f"Expected http_transport_abort_triggered log, got: {messages}"
        )
        assert any("http_transport_sockets_aborted" in m for m in messages), (
            f"Expected http_transport_sockets_aborted log, got: {messages}"
        )
        assert any("http_transport_session_recreated" in m for m in messages), (
            f"Expected http_transport_session_recreated log, got: {messages}"
        )
        assert any("http_transport_aborted_by_cancellation" in m for m in messages), (
            f"Expected http_transport_aborted_by_cancellation log, got: {messages}"
        )
        # Ensure no false-alarm network error was logged at ERROR level
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert not any("http_connection_failed" in r.getMessage() for r in error_records), (
            f"Unexpected http_connection_failed error logged during cancellation: {error_records}"
        )
    finally:
        server.stop_event.set()
        worker_thread.join(timeout=1.0)
