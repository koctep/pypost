"""Shared helpers for uvicorn lifecycle (bind errors, shutdown) in background threads."""

import asyncio
import errno


def format_bind_error(exc: OSError, host: str, port: int, server_name: str) -> str:
    """Return an operator-facing message for server bind failures."""
    if exc.errno in (errno.EADDRINUSE, errno.EADDRNOTAVAIL, 10048, 10013):
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
