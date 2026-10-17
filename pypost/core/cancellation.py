"""Cooperative cancellation tokens and adaptive backoff thread join (PYPOST-1437).

Provides lightweight cooperative cancellation primitives (CancellationTokenSource,
CancellationToken) and adaptive polling helpers (adaptive_thread_join, AdaptiveJoinPolicy)
for responsive, clean thread lifecycle management.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import logging
import threading
import time

logger = logging.getLogger(__name__)


class CancellationState(str, Enum):
    """Lifecycle states of a cancellation token."""

    ACTIVE = "active"
    CANCEL_REQUESTED = "cancel_requested"
    COMPLETED = "completed"


class OperationCancelledError(Exception):
    """Raised when an operation is cancelled via CancellationToken."""


class CancellationToken:
    """Read-only view of a cooperative cancellation signal."""

    def __init__(self, source: CancellationTokenSource) -> None:
        self._source = source

    @property
    def is_cancellation_requested(self) -> bool:
        """Return True if cancellation has been requested on the underlying source."""
        return self._source.is_cancellation_requested

    @property
    def cancellation_reason(self) -> str | None:
        """Return the reason provided during cancellation, if any."""
        return self._source.cancellation_reason

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for cancellation to be requested. Returns True if cancelled, False on timeout."""
        return self._source._event.wait(timeout)

    def register_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback to invoke when cancellation is requested.

        If cancellation has already been requested, the callback is invoked immediately.
        Returns a callable that unregisters the callback when invoked.
        """
        return self._source.register_callback(callback)

    def throw_if_cancellation_requested(self) -> None:
        """Raise OperationCancelledError if cancellation has been requested."""
        if self.is_cancellation_requested:
            raise OperationCancelledError(
                self.cancellation_reason or "Operation was cancelled."
            )


class CancellationTokenSource:
    """Owner and controller of a cooperative cancellation lifecycle."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._reason: str | None = None
        self._callbacks: list[Callable[[], None]] = []
        self._token = CancellationToken(self)
        self._disposed = False

    @property
    def token(self) -> CancellationToken:
        """Return the CancellationToken associated with this source."""
        return self._token

    @property
    def is_cancellation_requested(self) -> bool:
        """Return True if cancel() has been requested."""
        return self._event.is_set()

    @property
    def cancellation_reason(self) -> str | None:
        """Return the cancellation reason, if any."""
        with self._lock:
            return self._reason

    def cancel(self, reason: str | None = None) -> None:
        """Request cancellation and invoke all registered callbacks safely."""
        callbacks_to_run: list[Callable[[], None]] = []
        with self._lock:
            if self._disposed or self._event.is_set():
                return
            self._reason = reason or "Cancellation requested"
            self._event.set()
            callbacks_to_run = list(self._callbacks)
            self._callbacks.clear()

        logger.debug(
            "Cancellation requested for token source: reason=%s callbacks_count=%d",
            self._reason,
            len(callbacks_to_run),
        )

        for callback in callbacks_to_run:
            try:
                callback()
            except Exception:
                logger.exception("Error executing cancellation callback")

    def register_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback to run on cancellation, or invoke immediately if cancelled."""
        with self._lock:
            if self._event.is_set() and not self._disposed:
                try:
                    callback()
                except Exception:
                    logger.exception("Error executing immediate cancellation callback")

                def _noop() -> None:
                    pass

                return _noop

            if not self._disposed:
                self._callbacks.append(callback)

                def unregister() -> None:
                    with self._lock:
                        if callback in self._callbacks:
                            self._callbacks.remove(callback)

                return unregister

        def _noop_disposed() -> None:
            pass

        return _noop_disposed

    def dispose(self) -> None:
        """Release callback references and mark source disposed."""
        with self._lock:
            self._disposed = True
            self._callbacks.clear()

    def __enter__(self) -> CancellationTokenSource:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.dispose()


@dataclass(frozen=True)
class AdaptiveJoinPolicy:
    """Configuration for adaptive thread join polling."""

    initial_poll: float = 0.005
    multiplier: float = 1.5
    max_poll: float = 0.100
    default_timeout: float = 2.0
    progress_log_interval: float = 0.500


def adaptive_thread_join(
    thread: threading.Thread | None,
    timeout: float | None = None,
    *,
    policy: AdaptiveJoinPolicy | None = None,
    token: CancellationToken | None = None,
    thread_name: str | None = None,
) -> bool:
    """Join a thread using adaptive backoff polling and deadline enforcement.

    Returns True if the thread terminated within the timeout, False if it timed out.
    """
    if thread is None:
        return True
    if not thread.is_alive():
        return True

    active_policy = policy or AdaptiveJoinPolicy()
    max_timeout = timeout if timeout is not None else active_policy.default_timeout
    name = thread_name or getattr(thread, "name", "worker-thread")

    start_time = time.monotonic()
    deadline = start_time + max_timeout
    current_slice = active_policy.initial_poll
    last_log_time = start_time

    while time.monotonic() < deadline:
        now = time.monotonic()
        remaining = deadline - now
        if remaining <= 0:
            break

        slice_timeout = min(current_slice, remaining)
        logger.debug(
            "Adaptive thread join polling slice: thread=%s slice=%.4fs remaining=%.4fs",
            name,
            slice_timeout,
            remaining,
        )
        thread.join(timeout=slice_timeout)

        if not thread.is_alive():
            elapsed = time.monotonic() - start_time
            logger.debug(
                "Adaptive thread join succeeded: thread=%s elapsed=%.3fs timeout=%.3fs",
                name,
                elapsed,
                max_timeout,
            )
            return True

        if time.monotonic() - last_log_time >= active_policy.progress_log_interval:
            elapsed = time.monotonic() - start_time
            logger.info(
                "Waiting for worker thread to drain: thread=%s elapsed=%.3fs timeout=%.3fs",
                name,
                elapsed,
                max_timeout,
            )
            last_log_time = time.monotonic()

        current_slice = min(current_slice * active_policy.multiplier, active_policy.max_poll)

    # Reached deadline while thread is still running
    elapsed = time.monotonic() - start_time
    logger.warning(
        "Worker thread exceeded join deadline: thread=%s elapsed=%.3fs timeout=%.3fs alive=%s",
        name,
        elapsed,
        max_timeout,
        thread.is_alive(),
    )
    return False


__all__ = [
    "AdaptiveJoinPolicy",
    "CancellationState",
    "CancellationToken",
    "CancellationTokenSource",
    "OperationCancelledError",
    "adaptive_thread_join",
]
