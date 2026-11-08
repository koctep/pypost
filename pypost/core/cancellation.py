"""Cooperative cancellation tokens and adaptive backoff thread join (PYPOST-1437).

Provides lightweight cooperative cancellation primitives (CancellationTokenSource,
CancellationToken) and adaptive polling helpers (adaptive_thread_join, AdaptiveJoinPolicy)
for responsive, clean thread lifecycle management.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import inspect
import logging
import threading
import time
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

_R = TypeVar("_R")


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


def _is_thread_alive(thread: Any) -> bool:
    """Polymorphic check whether a thread or QThread worker is still alive."""
    if thread is None:
        return False
    is_alive_fn = getattr(thread, "is_alive", None)
    if callable(is_alive_fn):
        return bool(is_alive_fn())
    is_running_fn = getattr(thread, "isRunning", None) or getattr(thread, "is_running", None)
    if callable(is_running_fn):
        return bool(is_running_fn())
    is_finished_fn = getattr(thread, "isFinished", None)
    if callable(is_finished_fn):
        return not bool(is_finished_fn())
    return False


def _slice_join(thread: Any, slice_timeout: float) -> None:
    """Polymorphic join or wait helper for threading.Thread or QThread workers."""
    join_fn = getattr(thread, "join", None)
    if callable(join_fn):
        join_fn(timeout=slice_timeout)
        return
    wait_fn = getattr(thread, "wait", None)
    if callable(wait_fn):
        msecs = max(1, int(round(slice_timeout * 1000)))
        try:
            wait_fn(msecs)
        except TypeError:
            wait_fn(slice_timeout)


def _resolve_thread_name(thread: Any, thread_name: str | None = None) -> str:
    """Resolve thread name using explicit name, attribute, or class name."""
    if thread_name:
        return thread_name
    if thread is None:
        return "worker-thread"
    name_attr = getattr(thread, "name", None)
    if name_attr:
        return str(name_attr)
    obj_name_attr = getattr(thread, "objectName", None)
    if callable(obj_name_attr):
        obj_name = obj_name_attr()
        if obj_name:
            return str(obj_name)
    elif obj_name_attr:
        return str(obj_name_attr)
    return type(thread).__name__


def adaptive_thread_join(
    thread: Any | None,
    timeout: float | None = None,
    *,
    policy: AdaptiveJoinPolicy | None = None,
    token: CancellationToken | None = None,
    thread_name: str | None = None,
) -> bool:
    """Join a thread using adaptive backoff polling and deadline enforcement.

    Supports polymorphic duck-typed thread objects (threading.Thread, QThread, or doubles
    providing is_alive()/join() or isRunning()/wait()).

    Returns True if the thread terminated within the timeout, False if it timed out.
    """
    if thread is None:
        return True
    if not _is_thread_alive(thread):
        return True

    active_policy = policy or AdaptiveJoinPolicy()
    max_timeout = timeout if timeout is not None else active_policy.default_timeout
    name = _resolve_thread_name(thread, thread_name)

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
        _slice_join(thread, slice_timeout)

        if not _is_thread_alive(thread):
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
        _is_thread_alive(thread),
    )
    return False


def call_with_cancellation_token(
    fn: Callable[..., _R],
    *args: Any,
    cancellation_token: CancellationToken | None = None,
    **kwargs: Any,
) -> _R:
    """Invoke ``fn``, passing ``cancellation_token`` only when accepted.

    Falls back to calling without the token when the callable rejects the
    keyword (legacy duck-typed library services / test doubles).
    """
    if cancellation_token is None:
        return fn(*args, **kwargs)

    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        signature = None

    if signature is not None:
        params = signature.parameters
        accepts_var_kw = any(
            param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()
        )
        if not accepts_var_kw and "cancellation_token" not in params:
            return fn(*args, **kwargs)

    try:
        return fn(*args, cancellation_token=cancellation_token, **kwargs)
    except TypeError as exc:
        # MagicMock (*args, **kwargs) forwards kwargs into a strict side_effect.
        if "cancellation_token" not in str(exc):
            raise
        return fn(*args, **kwargs)


__all__ = [
    "AdaptiveJoinPolicy",
    "CancellationState",
    "CancellationToken",
    "CancellationTokenSource",
    "OperationCancelledError",
    "adaptive_thread_join",
    "call_with_cancellation_token",
]
