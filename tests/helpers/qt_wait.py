"""Bounded Qt event-loop polling helpers for tests."""

from __future__ import annotations

import time
from collections.abc import Callable

from PySide6.QtCore import QCoreApplication


def wait_until(
    condition: Callable[[], bool],
    *,
    timeout: float = 10.0,
    interval: float = 0.05,
    message: str = "condition not met within timeout",
) -> None:
    """Process Qt events until ``condition()`` is true or ``timeout`` elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        QCoreApplication.processEvents()
        if condition():
            return
        time.sleep(interval)
    raise TimeoutError(message)
