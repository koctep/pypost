"""Cross-process ephemeral TCP port allocation for parallel test runs."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import fcntl
import logging
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

logger = logging.getLogger(__name__)


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


def allocate_bound_tcp_socket(
    host: str = "127.0.0.1",
    *,
    reuse_addr: bool = True,
) -> socket.socket:
    """Bind and return an open TCP socket; caller owns close (PYPOST-1541/1546).

    Keeps the port reserved until the caller closes the socket or hands it to a
    server (e.g. uvicorn ``serve(sockets=[sock])``), eliminating the
    allocate-then-release TOCTOU of :func:`allocate_tcp_port`.

    Args:
        host: Bind address.
        reuse_addr: When True (default), set ``SO_REUSEADDR`` — suitable for
            in-process uvicorn socket handoff (PYPOST-1541). When False, bind
            exclusively so reuse-addr peers (uvicorn in other workers) cannot
            steal the port until :meth:`EphemeralPorts.release` (PYPOST-1546).
    """
    family = detect_address_family(host)
    clean_host = host.strip("[]")
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOCK_PATH, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            counter = _read_counter()
            for _ in range(_MAX_ATTEMPTS):
                counter += 1
                port = _PORT_BASE + (counter % _PORT_SPAN)
                sock = socket.socket(family, socket.SOCK_STREAM)
                if reuse_addr:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind((clean_host, port))
                except OSError:
                    sock.close()
                    continue
                _write_counter(counter)
                return sock

            sock = socket.socket(family, socket.SOCK_STREAM)
            if reuse_addr:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((clean_host, 0))
            _write_counter(counter + 1)
            return sock
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def allocate_tcp_port(host: str = "127.0.0.1") -> int:
    """Return a localhost TCP port unlikely to collide under parallel test workers.

    Prefer :func:`allocate_bound_tcp_socket` when the next step is a server bind;
    this helper still closes the probe socket before return (compat TOCTOU).
    """
    sock = allocate_bound_tcp_socket(host)
    try:
        return int(sock.getsockname()[1])
    finally:
        sock.close()


class EphemeralPorts(list):
    """``list[int]`` of reserved ports that stay exclusively bound until release.

    Process-mode tests must call :meth:`release` immediately before starting
    servers that will bind these ports (child uvicorn cannot inherit the hold).
    """

    def __init__(
        self,
        ports: list[int],
        socks: list[socket.socket],
        *,
        host: str,
    ) -> None:
        super().__init__(ports)
        self._socks = socks
        self._host = host
        self._released = False

    def release(self) -> None:
        """Close holder sockets so a process-mode server may bind the ports."""
        if self._released:
            return
        for sock in self._socks:
            try:
                sock.close()
            except OSError:
                pass
        self._socks.clear()
        self._released = True
        logger.debug(
            "ephemeral_ports_released host=%s count=%d ports=%s",
            self._host,
            len(self),
            list(self),
        )


class EphemeralPortReserve:
    """Manages batch allocation and reservation of distinct ephemeral ports."""

    def __init__(self, count: int, host: str = "127.0.0.1") -> None:
        self.count = count
        self.host = host
        self.ports: list[int] = []
        self._held: EphemeralPorts | None = None

    def allocate(self) -> EphemeralPorts:
        """Allocate ``count`` distinct ports and hold exclusive binds (PYPOST-1546)."""
        socks: list[socket.socket] = []
        ports: list[int] = []
        seen: set[int] = set()
        while len(socks) < self.count:
            sock = allocate_bound_tcp_socket(self.host, reuse_addr=False)
            port = int(sock.getsockname()[1])
            if port in seen:
                sock.close()
                continue
            seen.add(port)
            socks.append(sock)
            ports.append(port)
        held = EphemeralPorts(ports, socks, host=self.host)
        self._held = held
        self.ports = list(ports)
        logger.debug(
            "ephemeral_ports_allocated host=%s count=%d ports=%s",
            self.host,
            len(ports),
            ports,
        )
        return held

    def release(self) -> None:
        """Release exclusive holds (safe to call more than once)."""
        if self._held is not None:
            self._held.release()

    def verify_all_rebound(self, timeout: float = 2.0) -> bool:
        """Verify all allocated ports can be bound by raw TCP sockets (SO_REUSEADDR)."""
        self.release()
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
) -> Iterator[EphemeralPorts]:
    """Allocate exclusive ephemeral ports; call ``ports.release()`` before server bind.

    Holders stay open through test setup so parallel workers cannot steal ports.
    Process-mode suites must :meth:`EphemeralPorts.release` immediately before
    ``registry.start`` / runner start, then the child may bind.
    """
    reserve = EphemeralPortReserve(count, host)
    ports = reserve.allocate()
    try:
        yield ports
    finally:
        ports.release()
