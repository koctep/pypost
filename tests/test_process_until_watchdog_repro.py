"""PYPOST-1320: process_until must finish under QThread exc_info logging.

``process_until(..., use_poll_timer=False)`` while a background ``QThread`` is
inside ``logger.error(..., exc_info=True)`` must raise ``AssertionError`` within
about ``2× timeout_ms``. The GUI thread must not block in
``threading.Thread.start`` / ``_started.wait`` (or the limbo lock taken by that
``start``) past that bound.

Per-wait ``threading.Timer.start`` used to contend on
``threading._active_limbo_lock`` with DummyThread registration during
``exc_info`` formatting on an alien QThread — the hang class in Jira. The helper
now arms via a shared ``_DeadlineScheduler`` so the contended wait never calls
``Thread.start``.

This module forces that critical section (logging lock + limbo lock inside
``emit`` while formatting ``exc_info``) and asserts timely completion.
"""

from __future__ import annotations

import logging
import threading
import time

import pytest
from PySide6.QtCore import QThread

from tests.helpers.process_until import process_until

# GUI wait + forced contention; keep bound well under parallel worker timeout.
pytestmark = pytest.mark.timeout(30)

_TIMEOUT_MS = 300
# Finish within ~2× timeout_ms; allow small scheduling slack.
_EXIT_BOUND_S = (_TIMEOUT_MS / 1000.0) * 2 + 0.3
_LOGGER_NAME = "pypost.tests.pypost_1320_watchdog"


class _LimboHoldingExcInfoHandler(logging.Handler):
    """Handler that holds limbo during emit — mid-``exc_info`` DummyThread window."""

    def __init__(self, holding: threading.Event, release: threading.Event) -> None:
        super().__init__()
        self._holding = holding
        self._release = release
        self.setFormatter(
            logging.Formatter("%(asctime)s %(threadName)s %(message)s")
        )

    def emit(self, record: logging.LogRecord) -> None:
        # ``Logger.handle`` already holds ``logging._lock`` here (same as a normal
        # StreamHandler path while formatting ``exc_info`` / threadName).
        limbo = threading._active_limbo_lock
        limbo.acquire()
        try:
            # Touch DummyThread / thread-name paths under the limbo lock.
            threading.current_thread()
            self.format(record)
            self._holding.set()
            # Stay in the critical section until the test releases us.
            self._release.wait(timeout=60.0)
        finally:
            limbo.release()


class _ExcInfoLoggingWorker(QThread):
    """QThread that blocks inside ``logger.error(..., exc_info=True)``."""

    def __init__(self) -> None:
        super().__init__()
        self.holding = threading.Event()
        self.release = threading.Event()

    def run(self) -> None:
        log = logging.getLogger(_LOGGER_NAME)
        log.handlers.clear()
        log.propagate = False
        log.setLevel(logging.ERROR)
        log.addHandler(_LimboHoldingExcInfoHandler(self.holding, self.release))
        try:
            raise RuntimeError("pypost-1320 intentional worker error")
        except RuntimeError:
            log.error(
                "parse worker unexpected error (PYPOST-1320 repro)",
                exc_info=True,
            )


def test_process_until_exits_near_deadline_under_qthread_exc_info(
    qapp,
) -> None:
    """Hang-regression wait must finish while QThread is mid-exc_info logging.

    Warm up once without contention so the shared deadline scheduler bootstraps
    outside the race window; then force the logging/limbo critical section and
    require ``process_until(..., use_poll_timer=False)`` to raise
    ``AssertionError`` within ``_EXIT_BOUND_S``.
    """
    # Quiet warmup: start the long-lived scheduler so the contended arm never
    # calls Thread.start.
    process_until(lambda: True, timeout_ms=100)

    worker = _ExcInfoLoggingWorker()
    completed = threading.Event()
    timed_out = threading.Event()

    def _bound_watchdog() -> None:
        if not completed.wait(timeout=_EXIT_BOUND_S):
            timed_out.set()
            # Release limbo/logging so the GUI thread can unwind if hung.
            worker.release.set()

    watchdog = threading.Thread(
        target=_bound_watchdog,
        name="pypost-1320-exit-bound",
        daemon=True,
    )
    watchdog.start()

    worker.start()
    assert worker.holding.wait(timeout=5.0), (
        "QThread never entered logger.error(exc_info=True) critical section"
    )

    started = time.monotonic()
    try:
        with pytest.raises(AssertionError, match="condition not met within 300ms"):
            process_until(
                lambda: False,
                timeout_ms=_TIMEOUT_MS,
                use_poll_timer=False,
            )
    finally:
        completed.set()
        worker.release.set()
        if not worker.wait(5000):
            worker.terminate()
            worker.wait(2000)

    elapsed_s = time.monotonic() - started
    assert not timed_out.is_set(), (
        f"process_until hung under QThread exc_info logging for "
        f"{elapsed_s:.2f}s (bound {_EXIT_BOUND_S:.2f}s); GUI thread likely "
        f"blocked in Timer.start / threading limbo while the worker held "
        f"logging+limbo locks inside logger.error(..., exc_info=True)"
    )
    assert elapsed_s < _EXIT_BOUND_S, (
        f"wait exited after {elapsed_s:.2f}s; expected < {_EXIT_BOUND_S:.2f}s"
    )
