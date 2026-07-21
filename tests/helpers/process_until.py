"""Hang-resistant nested QEventLoop wait for gateway/worker tests.

Wall-clock deadline plus a daemon thread that posts ``loop.quit()`` onto the
GUI-thread event loop so a silent QTimer cannot hang ``exec()`` past the
deadline (PYPOST-823 / PYPOST-827). Distinct from ``qt_wait.wait_until``, which
polls via ``processEvents`` without nested ``exec()``.

Timeout AssertionError text can include a lazy diagnostic snapshot
(PYPOST-828).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol

from PySide6.QtCore import QEventLoop, QTimer

__all__ = [
    "format_storage_async_timeout_detail",
    "gateway_timeout_detail",
    "process_until",
]


class _WorkerRunning(Protocol):
    def isRunning(self) -> bool: ...


class _StorageAsyncGateway(Protocol):
    """Duck type for env/collection storage gateways in timeout detail."""

    _worker: _WorkerRunning | None

    def is_busy(self) -> bool: ...

    def has_pending_work(self) -> bool: ...


def format_storage_async_timeout_detail(
    *,
    is_busy: bool | None = None,
    has_pending_work: bool | None = None,
    worker_running: bool | None = None,
    worker_operation: str | None = None,
) -> str:
    """Format busy/pending and optional worker fields for timeout text.

    Omit None fields. Suitable for gateway waits (busy/pending required) and
    worker-only waits (busy/pending omitted; worker fields optional).
    """
    parts: list[str] = []
    if is_busy is not None:
        parts.append(f"busy={is_busy}")
    if has_pending_work is not None:
        parts.append(f"pending={has_pending_work}")
    if worker_running is not None:
        parts.append(f"worker_running={worker_running}")
    if worker_operation is not None:
        parts.append(f"worker_operation={worker_operation}")
    return " ".join(parts)


def gateway_timeout_detail(gateway: _StorageAsyncGateway) -> Callable[[], str]:
    """Lazy busy/pending (+ optional worker) snapshot for gateway waits."""

    def detail() -> str:
        worker = gateway._worker
        return format_storage_async_timeout_detail(
            is_busy=gateway.is_busy(),
            has_pending_work=gateway.has_pending_work(),
            worker_running=worker.isRunning() if worker is not None else False,
        )

    return detail


def process_until(
    predicate: Callable[[], bool],
    *,
    timeout_ms: int = 5_000,
    use_poll_timer: bool = True,
    timeout_detail: Callable[[], str] | None = None,
) -> None:
    """Pump nested QEventLoop until predicate() or wall-clock deadline.

    Posts ``loop.quit()`` from a daemon thread via
    ``QTimer.singleShot(0, loop, loop.quit)`` so a silent QTimer cannot hang
    ``exec()`` past the deadline.

    Args:
        predicate: Called until true or the deadline passes.
        timeout_ms: Wall-clock timeout in milliseconds.
        use_poll_timer: When False, rely only on the cross-thread posted quit
            (hang-regression proof when Qt timer slots never run).
        timeout_detail: Optional callable evaluated only on timeout; its return
            value is appended to the AssertionError text. Failures inside the
            callable are reported as a note and do not mask the timeout.

    Raises:
        AssertionError: predicate still false after the wait ends.
    """
    loop = QEventLoop()
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    timer = None

    if use_poll_timer:

        def tick() -> None:
            if predicate() or time.monotonic() >= deadline:
                loop.quit()

        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(tick)
        timer.start()

    # Cross-thread posted quit must target a QObject living on the GUI thread;
    # bare QTimer.singleShot from a worker thread would own the timer there
    # and never fire (no event loop on that thread).
    remaining_s = max(0.0, deadline - time.monotonic())

    def post_quit() -> None:
        QTimer.singleShot(0, loop, loop.quit)

    watchdog = threading.Timer(remaining_s, post_quit)
    watchdog.daemon = True
    watchdog.start()
    try:
        loop.exec()
    finally:
        watchdog.cancel()
        if timer is not None:
            timer.stop()

    if predicate():
        return

    detail_suffix = ""
    if timeout_detail is not None:
        try:
            detail_text = timeout_detail() or ""
        except Exception as exc:  # noqa: BLE001 - never mask timeout failure
            detail_text = f"timeout_detail failed: {type(exc).__name__}: {exc}"
        if detail_text:
            detail_suffix = f"; {detail_text}"

    raise AssertionError(
        f"condition not met within {timeout_ms}ms "
        f"(wall-clock deadline; predicate still false){detail_suffix}"
    )
