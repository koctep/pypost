"""Hang-resistant nested QEventLoop wait for gateway/worker tests.

Wall-clock deadline plus a daemon thread that posts ``loop.quit()`` onto the
GUI-thread event loop so a silent QTimer cannot hang ``exec()`` past the
deadline (PYPOST-823 / PYPOST-827). Distinct from ``qt_wait.wait_until``, which
polls via ``processEvents`` without nested ``exec()``.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from PySide6.QtCore import QEventLoop, QTimer

__all__ = ["process_until"]


def process_until(
    predicate: Callable[[], bool],
    *,
    timeout_ms: int = 5_000,
    use_poll_timer: bool = True,
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

    assert predicate(), (
        f"condition not met within {timeout_ms}ms "
        "(wall-clock deadline; load_completed/load_failed or predicate never true)"
    )
