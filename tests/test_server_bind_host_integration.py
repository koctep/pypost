"""Integration tests: MCP and metrics servers bind to configured host (PYPOST-150)."""

import pytest

pytestmark = pytest.mark.timeout(120)

import re
import shutil
import socket
import subprocess
import time
import unittest
from dataclasses import dataclass

from PySide6.QtCore import QCoreApplication

from pypost.core.qt.metrics import MetricsManager
from pypost.core.qt.mcp_server import MCPServerManager

@dataclass(frozen=True)
class BindHostCase:
    bind_host: str
    client_host: str
    expected_listen: frozenset[str]

BIND_HOST_CASES = (
    BindHostCase("127.0.0.1", "127.0.0.1", frozenset({"127.0.0.1"})),
    BindHostCase("0.0.0.0", "127.0.0.1", frozenset({"0.0.0.0"})),
    BindHostCase("localhost", "127.0.0.1", frozenset({"127.0.0.1"})),
    BindHostCase("::1", "::1", frozenset({"::1"})),
)

def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

def _wait_for_listen(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        QCoreApplication.processEvents()
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"Server did not listen on {host}:{port} within {timeout}s")

def _listen_addresses_for_port(port: int) -> set[str]:
    if shutil.which("lsof") is None:
        return set()
    proc = subprocess.run(
        ["lsof", f"-iTCP:{port}", "-sTCP:LISTEN", "-n", "-P"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if proc.returncode != 0:
        return set()
    suffix = f":{port}"
    addresses: set[str] = set()
    pattern = re.compile(r"(\S+)" + re.escape(suffix) + r"\s+\(LISTEN\)")
    for line in proc.stdout.splitlines()[1:]:
        match = pattern.search(line)
        if not match:
            continue
        raw = match.group(1)
        if raw == "*":
            addresses.add("0.0.0.0")
        elif raw.startswith("[") and raw.endswith("]"):
            addresses.add(raw[1:-1])
        else:
            addresses.add(raw)
    return addresses

def _assert_listen_address(port: int, expected: frozenset[str]) -> None:
    observed = _listen_addresses_for_port(port)
    if not observed:
        return
    assert observed & set(expected), (
        f"Expected listen on one of {sorted(expected)}, observed {sorted(observed)}"
    )

@pytest.mark.usefixtures("qapp")

class TestMcpServerBindHost(unittest.TestCase):
    def _run_case(self, case: BindHostCase) -> None:
        port = _free_port()
        manager = MCPServerManager()
        manager.start_server(port, [], host=case.bind_host)
        try:
            _wait_for_listen(case.client_host, port)
            _assert_listen_address(port, case.expected_listen)
        finally:
            manager.stop_server()

    def test_binds_to_127_0_0_1(self):
        self._run_case(BIND_HOST_CASES[0])

    def test_binds_to_0_0_0_0(self):
        self._run_case(BIND_HOST_CASES[1])

    def test_binds_to_localhost(self):
        self._run_case(BIND_HOST_CASES[2])

    def test_binds_to_ipv6_loopback(self):
        self._run_case(BIND_HOST_CASES[3])

@pytest.mark.usefixtures("qapp")

class TestMetricsServerBindHost(unittest.TestCase):
    def _run_case(self, case: BindHostCase) -> None:
        port = _free_port()
        manager = MetricsManager()
        manager.start_server(case.bind_host, port)
        try:
            _wait_for_listen(case.client_host, port)
            _assert_listen_address(port, case.expected_listen)
        finally:
            manager.stop_server()

    def test_binds_to_127_0_0_1(self):
        self._run_case(BIND_HOST_CASES[0])

    def test_binds_to_0_0_0_0(self):
        self._run_case(BIND_HOST_CASES[1])

    def test_binds_to_localhost(self):
        self._run_case(BIND_HOST_CASES[2])

    def test_binds_to_ipv6_loopback(self):
        self._run_case(BIND_HOST_CASES[3])

if __name__ == "__main__":
    unittest.main()
