"""Cross-process ephemeral TCP port allocation for parallel test runs."""

from __future__ import annotations

import fcntl
import os
import socket
from pathlib import Path

_LOCK_PATH = Path(os.environ.get("PYPOST_TEST_PORT_LOCK", "/tmp/pypost-test-port.lock"))
_COUNTER_PATH = _LOCK_PATH.with_suffix(".counter")
_PORT_BASE = 35_000
_PORT_SPAN = 25_000
_MAX_ATTEMPTS = 200


def _read_counter() -> int:
    if not _COUNTER_PATH.is_file():
        return 0
    try:
        return int(_COUNTER_PATH.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        return 0


def _write_counter(value: int) -> None:
    _COUNTER_PATH.write_text(f"{value}\n", encoding="utf-8")


def _can_bind(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def allocate_tcp_port(host: str = "127.0.0.1") -> int:
    """Return a localhost TCP port unlikely to collide under parallel test workers."""
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOCK_PATH, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            counter = _read_counter()
            for _ in range(_MAX_ATTEMPTS):
                counter += 1
                port = _PORT_BASE + (counter % _PORT_SPAN)
                if _can_bind(host, port):
                    _write_counter(counter)
                    return port

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, 0))
                port = sock.getsockname()[1]
            _write_counter(counter + 1)
            return port
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
