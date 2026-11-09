"""Multi-step exclusive port hold contract (PYPOST-1508).

``test_process_mode_variable_isolation_under_concurrent_load`` previously
called ``reserve.release()`` inside the upsert loop after the first server,
freeing ports 2..N while remaining upserts still ran (EADDRINUSE under
parallel workers). Contract: exclusive holds survive every setup step until
a single ``release()`` after the last step (release-before-start handoff).
"""

from __future__ import annotations

import socket

import pytest

from tests.helpers.port_allocation import reserve_ephemeral_ports

pytestmark = pytest.mark.timeout(30)

_SETUP_STEPS = 3


def _reuseaddr_bind(port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
        sock.listen(1)
    finally:
        sock.close()


@pytest.mark.timeout(30)
def test_batch_ports_stay_held_across_all_multi_server_setup_steps() -> None:
    """Exclusive ports must reject reuse-addr thieves after every setup step.

    Mirrors the isolation upsert loop. Early ``release()`` after the first of
    N steps (pre-fix anti-pattern) must not leave remaining ports free while
    later setup steps still run.
    """
    with reserve_ephemeral_ports(_SETUP_STEPS) as ports:
        for step in range(_SETUP_STEPS):
            # Stand-in for upsert / registry work while holders must stay open.
            _ = step
            for port in ports:
                with pytest.raises(OSError):
                    _reuseaddr_bind(port)

        # Single handoff after full setup — child bind must succeed.
        ports.release()
        for port in ports:
            _reuseaddr_bind(port)
