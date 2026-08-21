"""Shared helpers for uvicorn lifecycle (bind errors, shutdown) in background threads."""
from __future__ import annotations

import asyncio
import errno
import sys
import threading
from collections.abc import Callable
from typing import Any, cast

_process_exit_lock = threading.Lock()
_process_exit_local = threading.local()
_process_exit_original: Callable[[Any], Any] | None = None
_process_exit_users = 0


def _dispatch_process_exit(code: Any = 0) -> Any:
    handler = getattr(_process_exit_local, "handler", None)
    if handler is not None:
        return handler(code)
    assert _process_exit_original is not None
    return _process_exit_original(code)


def install_thread_exit(handler: Callable[[Any], Any]) -> None:
    global _process_exit_original, _process_exit_users
    with _process_exit_lock:
        if _process_exit_users == 0:
            _process_exit_original = sys.exit
            sys.exit = cast(Any, _dispatch_process_exit)
        _process_exit_users += 1
    _process_exit_local.handler = handler


def uninstall_thread_exit() -> None:
    global _process_exit_original, _process_exit_users
    if hasattr(_process_exit_local, "handler"):
        del _process_exit_local.handler
    with _process_exit_lock:
        _process_exit_users -= 1
        if _process_exit_users == 0:
            if sys.exit is _dispatch_process_exit and _process_exit_original is not None:
                sys.exit = cast(Any, _process_exit_original)
            _process_exit_original = None


def get_process_exit_original() -> Callable[[Any], Any] | None:
    return _process_exit_original


def format_bind_error(exc: OSError, host: str, port: int, server_name: str) -> str:
    """Return an operator-facing message for server bind failures."""
    if (
        exc.errno in (errno.EADDRINUSE, errno.EADDRNOTAVAIL, 48, 49, 10048, 10013)
        or "address already in use" in str(exc).lower()
    ):
        return (
            f"Cannot start {server_name} on {host}:{port}: port is busy or unavailable. "
            "Choose another port in Settings or stop the process using this port."
        )
    return f"Cannot start {server_name} on {host}:{port}: {exc.strerror or exc}"


def drain_pending_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel and await any tasks still pending on ``loop`` before closing it.

    SSE transports (sse_starlette) spawn a long-lived ``_shutdown_watcher`` task per
    event loop that only exits on its next 0.5s poll. Closing the loop while it (or
    any other background task) is still pending causes asyncio to log "Task was
    destroyed but it is pending!" when the orphaned Task is garbage-collected. Call
    this right before ``loop.close()`` to cancel and let such tasks unwind cleanly.
    """
    pending = asyncio.all_tasks(loop)
    if not pending:
        return
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
