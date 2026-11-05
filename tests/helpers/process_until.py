"""Hang-resistant nested QEventLoop wait for gateway/worker tests.

Wall-clock deadline plus a module-scoped daemon deadline scheduler that posts
``loop.quit()`` onto the GUI-thread event loop so a silent QTimer cannot hang
``exec()`` past the deadline (PYPOST-823 / PYPOST-827 / PYPOST-1320). Distinct
from ``qt_wait.wait_until``, which polls via ``processEvents`` without nested
``exec()``.

Timeout AssertionError text can include a lazy diagnostic snapshot
(PYPOST-828).
"""

from __future__ import annotations

import heapq
import itertools
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
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
    """Lazy busy/pending (+ optional worker) snapshot for gateway waits.

    Includes ``worker_operation=…`` when the attached worker exposes a string
    ``_operation`` (env load/save). Collection load-only workers omit it.
    """

    def detail() -> str:
        worker = gateway._worker
        operation = getattr(worker, "_operation", None) if worker is not None else None
        return format_storage_async_timeout_detail(
            is_busy=gateway.is_busy(),
            has_pending_work=gateway.has_pending_work(),
            worker_running=worker.isRunning() if worker is not None else False,
            worker_operation=operation if isinstance(operation, str) else None,
        )

    return detail


@dataclass(order=True)
class _DeadlineEntry:
    """Heap entry for a cancellable posted-quit deadline."""

    deadline: float
    seq: int
    cancelled: bool = field(default=False, compare=False)
    callback: Callable[[], None] | None = field(default=None, compare=False)


class _DeadlineScheduler:
    """Single daemon thread that fires wall-clock callbacks without per-arm start.

    ``process_until`` must not call ``threading.Thread.start`` on the hot path
    while a QThread may hold logging / limbo locks (PYPOST-1320). Bootstrap
    happens once on first arm; later arms only enqueue under a Condition.
    """

    def __init__(self) -> None:
        self._cv = threading.Condition()
        self._heap: list[_DeadlineEntry] = []
        self._seq = itertools.count()
        self._thread: threading.Thread | None = None

    def arm(self, delay_s: float, callback: Callable[[], None]) -> Callable[[], None]:
        """Schedule ``callback`` after ``delay_s``; return a cancel callable."""
        self._ensure_started()
        deadline = time.monotonic() + max(0.0, delay_s)
        with self._cv:
            entry = _DeadlineEntry(
                deadline=deadline,
                seq=next(self._seq),
                callback=callback,
            )
            heapq.heappush(self._heap, entry)
            self._cv.notify()

        def cancel() -> None:
            with self._cv:
                entry.cancelled = True
                entry.callback = None
                self._cv.notify()

        return cancel

    def _ensure_started(self) -> None:
        with self._cv:
            if self._thread is not None:
                return
            thread = threading.Thread(
                target=self._run,
                name="process-until-deadline",
                daemon=True,
            )
            self._thread = thread
            thread.start()

    def _run(self) -> None:
        while True:
            callback: Callable[[], None] | None = None
            with self._cv:
                while True:
                    while self._heap and self._heap[0].cancelled:
                        heapq.heappop(self._heap)
                    if not self._heap:
                        self._cv.wait()
                        continue
                    now = time.monotonic()
                    remaining = self._heap[0].deadline - now
                    if remaining > 0:
                        self._cv.wait(timeout=remaining)
                        continue
                    entry = heapq.heappop(self._heap)
                    if not entry.cancelled:
                        callback = entry.callback
                    break
            if callback is not None:
                callback()


_deadline_scheduler = _DeadlineScheduler()


def _arm_posted_quit(loop: QEventLoop, remaining_s: float) -> Callable[[], None]:
    """Schedule GUI-thread ``loop.quit`` after ``remaining_s``; return cancel.

    Must not call ``threading.Thread.start`` on the per-wait path after the
    shared deadline scheduler has bootstrapped.
    """

    def post_quit() -> None:
        QTimer.singleShot(0, loop, loop.quit)

    return _deadline_scheduler.arm(remaining_s, post_quit)


def process_until(
    predicate: Callable[[], bool],
    *,
    timeout_ms: int = 5_000,
    use_poll_timer: bool = True,
    timeout_detail: Callable[[], str] | None = None,
) -> None:
    """Pump nested QEventLoop until predicate() or wall-clock deadline.

    Posts ``loop.quit()`` from the shared deadline scheduler via
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
    cancel_watchdog = _arm_posted_quit(loop, remaining_s)
    try:
        loop.exec()
    finally:
        cancel_watchdog()
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
