"""Automated test for adaptive thread join and cancellation tokens (PYPOST-1437).

Asserts contracts defined in ai-tasks/PYPOST-1437/20-architecture.md:
- Importability and behavior of CancellationToken, CancellationTokenSource, AdaptiveJoinPolicy,
  and adaptive_thread_join in pypost.core.cancellation.
- Fast return latency (<50ms) for quickly-exiting worker threads without sleeping rigid 2.0s.
- Progressive adaptive polling backoff on extended ASGI connection/task drain.
- Timeout boundary enforcement and diagnostic warning emission on uncooperative worker threads.
- MCPServerManager.stop_server integration and cooperative cancellation token propagation.
"""

from __future__ import annotations

import logging
import threading
import time
from unittest.mock import MagicMock

import pytest

from pypost.core.cancellation import (
    AdaptiveJoinPolicy,
    CancellationTokenSource,
    OperationCancelledError,
    adaptive_thread_join,
)
from pypost.core.qt.mcp_server import MCPServerManager

pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(10)
def test_cancellation_token_cooperative_lifecycle() -> None:
    """Validate cooperative cancellation token signaling, states, and registered callbacks."""
    source = CancellationTokenSource()
    token = source.token

    assert token.is_cancellation_requested is False
    assert token.cancellation_reason is None

    callback_called: list[bool] = []

    def on_cancel() -> None:
        callback_called.append(True)

    unregister = token.register_callback(on_cancel)

    # Cooperative wait before cancellation times out
    assert token.wait(timeout=0.01) is False

    # Cancel source
    source.cancel(reason="test cooperative stop")
    assert token.is_cancellation_requested is True
    assert token.cancellation_reason == "test cooperative stop"
    assert len(callback_called) == 1

    # Unregister after cancel is safe no-op
    unregister()

    # Subsequent wait returns immediately True
    assert token.wait(timeout=1.0) is True

    # throw_if_cancellation_requested raises OperationCancelledError
    with pytest.raises(OperationCancelledError):
        token.throw_if_cancellation_requested()

    source.dispose()


@pytest.mark.timeout(10)
def test_adaptive_thread_join_fast_return_latency() -> None:
    """Validate that adaptive_thread_join returns promptly (<50ms) when thread finishes quickly."""
    def quick_worker() -> None:
        time.sleep(0.010)

    thread = threading.Thread(target=quick_worker, daemon=True)
    thread.start()

    start_time = time.monotonic()
    joined = adaptive_thread_join(thread, timeout=2.0)
    elapsed = time.monotonic() - start_time

    assert joined is True
    assert not thread.is_alive()
    # Must exit promptly and not block for the full 2.0s timeout
    assert elapsed < 0.150, f"Adaptive join took too long: {elapsed:.3f}s"


@pytest.mark.timeout(10)
def test_adaptive_thread_join_progressive_polling_on_slow_drain() -> None:
    """Validate adaptive polling backoff across simulated 200ms ASGI task drain."""
    def draining_worker() -> None:
        time.sleep(0.200)

    thread = threading.Thread(target=draining_worker, daemon=True)
    thread.start()

    start_time = time.monotonic()
    joined = adaptive_thread_join(
        thread,
        timeout=1.0,
        policy=AdaptiveJoinPolicy(initial_poll=0.005, multiplier=1.5, max_poll=0.050),
    )
    elapsed = time.monotonic() - start_time

    assert joined is True
    assert not thread.is_alive()
    assert 0.180 <= elapsed < 0.500, (
        f"Adaptive join completed outside expected window: {elapsed:.3f}s"
    )


@pytest.mark.timeout(10)
def test_adaptive_thread_join_timeout_boundary_and_diagnostics(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validate deadline enforcement and diagnostic warning when thread refuses to terminate."""
    never_stop = threading.Event()

    def stuck_worker() -> None:
        never_stop.wait(5.0)

    thread = threading.Thread(target=stuck_worker, daemon=True, name="stuck-worker-test")
    thread.start()

    try:
        with caplog.at_level(logging.WARNING):
            start_time = time.monotonic()
            joined = adaptive_thread_join(
                thread,
                timeout=0.080,
                policy=AdaptiveJoinPolicy(initial_poll=0.005, multiplier=1.5, max_poll=0.020),
                thread_name="stuck-worker-test",
            )
            elapsed = time.monotonic() - start_time

        assert joined is False
        assert thread.is_alive()
        assert 0.070 <= elapsed < 0.250, f"Timeout boundary elapsed outside range: {elapsed:.3f}s"

        # Diagnostic warning must be emitted
        warning_records = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING and "stuck-worker-test" in r.message
        ]
        assert len(warning_records) >= 1
    finally:
        never_stop.set()
        thread.join(timeout=1.0)


@pytest.mark.timeout(10)
def test_mcp_server_manager_stop_server_adaptive_join_integration() -> None:
    """Validate MCPServerManager.stop_server uses adaptive join and cancellation token."""
    manager = MCPServerManager()
    assert manager.is_running() is False

    # Calling stop_server on non-running server returns cleanly without error
    result = manager.stop_server(timeout=1.0)
    assert result is True

    # 1. Simulate running server with quickly-exiting thread
    quick_event = threading.Event()

    def quick_worker() -> None:
        quick_event.wait(0.010)

    thread = threading.Thread(target=quick_worker, daemon=True)
    thread.start()
    manager._server_thread = thread
    manager._server_instance = MagicMock()
    cts = CancellationTokenSource()
    cancelled_log: list[str] = []
    cts.token.register_callback(lambda: cancelled_log.append("cancelled"))
    manager._cancellation_source = cts

    res = manager.stop_server(timeout=1.0)
    assert res is True
    assert manager._server_thread is None
    assert cancelled_log == ["cancelled"]
    assert manager.is_running() is False

    # 2. Simulate uncooperative worker thread: stop_server must not clear thread on timeout
    stuck_event = threading.Event()

    def uncooperative_worker() -> None:
        stuck_event.wait(5.0)

    stuck_thread = threading.Thread(target=uncooperative_worker, daemon=True)
    stuck_thread.start()
    try:
        manager._server_thread = stuck_thread
        manager._server_instance = MagicMock()
        manager._cancellation_source = CancellationTokenSource()

        res_stuck = manager.stop_server(timeout=0.050)
        assert res_stuck is False
        assert manager._server_thread is not None
        assert manager._server_thread.is_alive()
        assert manager.is_running() is True
    finally:
        stuck_event.set()
        stuck_thread.join(timeout=1.0)
