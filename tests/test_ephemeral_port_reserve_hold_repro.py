"""Deterministic repro for batch ephemeral port TOCTOU (PYPOST-1546).

Process-mode suites reserve integer ports via ``reserve_ephemeral_ports`` then
start child uvicorn workers later. Ports must stay exclusively held against
``SO_REUSEADDR`` thieves until ``release()`` hands them off for bind.
"""

from __future__ import annotations

import socket

import pytest

from tests.helpers.port_allocation import reserve_ephemeral_ports

pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(30)
def test_reserve_ephemeral_ports_holds_exclusively_against_reuseaddr_thief() -> None:
    """Reserved ports must reject reuse-addr peers until release()."""
    with reserve_ephemeral_ports(1) as ports:
        port = ports[0]
        thief = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        thief.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            with pytest.raises(OSError):
                thief.bind(("127.0.0.1", port))
        finally:
            thief.close()

        ports.release()

        child = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        child.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            child.bind(("127.0.0.1", port))
            child.listen(1)
        finally:
            child.close()
