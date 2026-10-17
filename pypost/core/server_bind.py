"""Shared helpers for uvicorn lifecycle (bind errors, shutdown) in background threads."""
from __future__ import annotations

import asyncio
import enum
import errno
import ipaddress
import logging
import socket
import sys
import threading
from collections.abc import Callable
from typing import Any, cast

logger = logging.getLogger(__name__)


__all__ = [
    "BindErrorClassification",
    "classify_bind_error",
    "extract_errno",
    "format_bind_error",
    "detect_address_family",
    "validate_host_and_port",
]


class BindErrorClassification(str, enum.Enum):
    PORT_IN_USE = "port_in_use"
    ADDRESS_NOT_AVAILABLE = "address_not_available"
    PERMISSION_DENIED = "permission_denied"
    UNCLASSIFIED = "unclassified"


ERRNO_PORT_IN_USE: frozenset[int] = frozenset({
    getattr(errno, "EADDRINUSE", 98),
    98,
    48,       # BSD / macOS EADDRINUSE
    10048,    # Windows WSAEADDRINUSE
})

ERRNO_ADDR_NOT_AVAIL: frozenset[int] = frozenset({
    getattr(errno, "EADDRNOTAVAIL", 99),
    99,
    49,       # BSD / macOS EADDRNOTAVAIL
    10049,    # Windows WSAEADDRNOTAVAIL
})

ERRNO_PERMISSION_DENIED: frozenset[int] = frozenset({
    getattr(errno, "EACCES", 13),
    getattr(errno, "EPERM", 1),
    13,
    1,
    10013,    # Windows WSAEACCES
})


def extract_errno(exc: BaseException) -> int | None:
    """Extract numeric OS error code from an exception."""
    err = getattr(exc, "errno", None)
    if isinstance(err, int):
        return err
    winerr = getattr(exc, "winerror", None)
    if isinstance(winerr, int):
        return winerr
    args = getattr(exc, "args", ())
    if args and len(args) >= 1:
        first = args[0]
        if isinstance(first, int):
            return first
        if isinstance(first, tuple) and len(first) >= 1 and isinstance(first[0], int):
            return first[0]
    return None


def classify_bind_error(exc: BaseException) -> BindErrorClassification:
    """Classify an OS networking exception into a structured category."""
    err = extract_errno(exc)
    if err is not None:
        if err in ERRNO_PORT_IN_USE:
            return BindErrorClassification.PORT_IN_USE
        if err in ERRNO_ADDR_NOT_AVAIL:
            return BindErrorClassification.ADDRESS_NOT_AVAILABLE
        if err in ERRNO_PERMISSION_DENIED:
            return BindErrorClassification.PERMISSION_DENIED
    return BindErrorClassification.UNCLASSIFIED


def detect_address_family(host: str) -> socket.AddressFamily:
    """Detect whether host string requires AF_INET or AF_INET6."""
    clean_host = host.strip("[]")
    family: socket.AddressFamily
    try:
        ip = ipaddress.ip_address(clean_host)
        family = socket.AF_INET6 if ip.version == 6 else socket.AF_INET
    except ValueError:
        family = socket.AF_INET6 if ":" in clean_host else socket.AF_INET
    logger.debug("detect_address_family host=%s family=%s", host, family.name)
    return family


def validate_host_and_port(host: str, port: int) -> None:
    """Preflight socket bind on host:port, raising ValueError on bind conflict."""
    family = detect_address_family(host)
    raw_host = host.strip("[]")
    logger.debug(
        "validate_host_and_port_probing host=%s port=%d family=%s",
        host,
        port,
        family.name,
    )
    try:
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            if hasattr(socket, "SO_REUSEADDR"):
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind((raw_host, port))
        logger.info("validate_host_and_port_succeeded host=%s port=%d", host, port)
    except OSError as exc:
        classification = classify_bind_error(exc)
        err_msg = format_bind_error(exc, host, port, server_label="server")
        if classification in (
            BindErrorClassification.PORT_IN_USE,
            BindErrorClassification.PERMISSION_DENIED,
            BindErrorClassification.ADDRESS_NOT_AVAILABLE,
        ):
            logger.warning(
                "validate_host_and_port_failed host=%s port=%d classification=%s error=%s",
                host,
                port,
                classification.value,
                exc,
            )
        else:
            logger.error(
                "validate_host_and_port_unclassified_error host=%s port=%d error=%s",
                host,
                port,
                exc,
            )
        raise ValueError(
            f"Port {port} on {host} is unavailable ({classification.value}): {err_msg}"
        ) from exc


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


def format_bind_error(
    host_or_exc: BaseException | str,
    port_or_host: int | str,
    exc_or_port: BaseException | int | None = None,
    server_label: str = "server",
    *,
    server_name: str | None = None,
) -> str:
    """Return an operator-facing message for server bind failures without substring matching."""
    name = server_name if server_name is not None else server_label

    exc: BaseException
    host: str
    port: int

    if isinstance(host_or_exc, BaseException):
        exc = host_or_exc
        host = str(port_or_host)
        if isinstance(exc_or_port, int):
            port = exc_or_port
        elif isinstance(exc_or_port, str) and exc_or_port.isdigit():
            port = int(exc_or_port)
        else:
            port = 0
    elif isinstance(port_or_host, int) or (
        isinstance(port_or_host, str)
        and port_or_host.isdigit()
        and isinstance(exc_or_port, BaseException)
    ):
        host = str(host_or_exc)
        port = int(port_or_host)
        exc = (
            exc_or_port
            if isinstance(exc_or_port, BaseException)
            else Exception(str(exc_or_port))
        )
    elif isinstance(exc_or_port, int) or (
        isinstance(exc_or_port, str) and str(exc_or_port).isdigit()
    ):
        exc = Exception(str(host_or_exc))
        host = str(port_or_host)
        port = int(exc_or_port) if isinstance(exc_or_port, int) else int(str(exc_or_port))
    else:
        host = str(host_or_exc)
        port = port_or_host if isinstance(port_or_host, int) else 0
        exc = (
            exc_or_port
            if isinstance(exc_or_port, BaseException)
            else Exception(str(exc_or_port))
        )

    classification = classify_bind_error(exc)
    details = getattr(exc, "strerror", None) or str(exc)

    if classification == BindErrorClassification.PORT_IN_USE:
        return (
            f"Cannot start {name} on {host}:{port}: port is busy or unavailable. "
            "Choose another port in Settings or stop the process using this port."
        )
    if classification == BindErrorClassification.PERMISSION_DENIED:
        return (
            f"Cannot start {name} on {host}:{port}: permission denied "
            f"(insufficient privileges or restricted port). {details}"
        )
    if classification == BindErrorClassification.ADDRESS_NOT_AVAILABLE:
        return (
            f"Cannot start {name} on {host}:{port}: address not available. "
            f"The requested host interface cannot be bound on this system. {details}"
        )
    return f"Cannot start {name} on {host}:{port}: {details}"


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
