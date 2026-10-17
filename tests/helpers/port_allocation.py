"""Cross-process ephemeral TCP port allocation for parallel test runs."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import socket
import time

from pypost.core.server_bind import detect_address_family

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
    family = detect_address_family(host)
    clean_host = host.strip("[]")
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((clean_host, port))
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

            family = detect_address_family(host)
            clean_host = host.strip("[]")
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((clean_host, 0))
                port = int(sock.getsockname()[1])
            _write_counter(counter + 1)
            return port
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


class EphemeralPortReserve:
    """Manages batch allocation and reservation of distinct ephemeral ports."""

    def __init__(self, count: int, host: str = "127.0.0.1") -> None:
        self.count = count
        self.host = host
        self.ports: list[int] = []

    def allocate(self) -> list[int]:
        """Allocate 'count' distinct, verified bindable ports atomically."""
        allocated: set[int] = set()
        while len(allocated) < self.count:
            port = allocate_tcp_port(self.host)
            allocated.add(port)
        self.ports = sorted(allocated)
        return list(self.ports)

    def verify_all_rebound(self, timeout: float = 2.0) -> bool:
        """Verify all allocated ports can be bound by raw TCP sockets (SO_REUSEADDR)."""
        deadline = time.monotonic() + timeout
        for port in self.ports:
            bound = False
            while time.monotonic() <= deadline:
                if _can_bind(self.host, port):
                    bound = True
                    break
                time.sleep(0.01)
            if not bound:
                return False
        return True


@contextmanager
def reserve_ephemeral_ports(
    count: int, host: str = "127.0.0.1"
) -> Iterator[list[int]]:
    """Context manager allocating and managing a batch of ephemeral ports."""
    reserve = EphemeralPortReserve(count, host)
    ports = reserve.allocate()
    try:
        yield ports
    finally:
        pass
