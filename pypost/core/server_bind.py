"""Shared helpers for uvicorn bind failures in background threads."""

import errno


def format_bind_error(exc: OSError, host: str, port: int, server_name: str) -> str:
    """Return an operator-facing message for server bind failures."""
    if exc.errno in (errno.EADDRINUSE, errno.EADDRNOTAVAIL, 10048, 10013):
        return (
            f"Cannot start {server_name} on {host}:{port}: port is busy or unavailable. "
            "Choose another port in Settings or stop the process using this port."
        )
    return f"Cannot start {server_name} on {host}:{port}: {exc.strerror or exc}"
