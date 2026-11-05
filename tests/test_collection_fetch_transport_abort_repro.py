"""PYPOST-1425: transport-level abort on CollectionFetchWorker / ManifestDiscoveryWorker cancel.

Desired behavior: cancel() must abort in-flight library I/O via CancellationToken
callbacks (socket/session close), so the worker exits promptly instead of waiting for
the full remote read. Generation discard alone is insufficient.
"""
from __future__ import annotations

import threading
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from pypost.core.cancellation import OperationCancelledError
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection
from pypost.ui.workers.collection_fetch_worker import CollectionFetchWorker
from pypost.ui.workers.manifest_discovery_worker import ManifestDiscoveryWorker

pytestmark = pytest.mark.timeout(30)

BLOCK_BUDGET_S = 5.0
ABORT_ELAPSED_LIMIT_S = 0.5


def _ensure_qapp() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.mark.timeout(30)
def test_collection_fetch_worker_cancel_aborts_transport() -> None:
    """cancel() must fire transport abort callbacks and unblock read_collection promptly."""
    _ensure_qapp()

    entered = threading.Event()
    aborted = threading.Event()
    col = Collection(
        name="RemoteCol",
        variables=[CollectionVariable(name="host", type="string", default="api")],
    )

    def blocking_read(
        connection_id: str,
        collection_path: str,
        cancellation_token: Any = None,
    ) -> Collection:
        entered.set()
        if cancellation_token is not None:
            cancellation_token.register_callback(aborted.set)
            # Block until transport abort closes the simulated socket, or budget elapses.
            if aborted.wait(timeout=BLOCK_BUDGET_S):
                raise OperationCancelledError("socket closed by abort")
            return col
        # Pre-fix path: no token — cancel cannot unblock this sleep.
        time.sleep(BLOCK_BUDGET_S)
        return col

    service = MagicMock()
    service.read_collection.side_effect = blocking_read

    worker = CollectionFetchWorker(
        library_service=service,
        connection_id="conn_1",
        collection_path="cols/remote.json",
        generation_id=1,
    )
    worker.start()

    assert entered.wait(timeout=2.0), "read_collection must start before cancel"
    t0 = time.monotonic()
    worker.cancel()
    finished = worker.wait(int(ABORT_ELAPSED_LIMIT_S * 1000) + 500)
    elapsed = time.monotonic() - t0

    assert finished, "worker must finish promptly after cancel"
    assert elapsed < ABORT_ELAPSED_LIMIT_S, (
        f"cancel must abort transport promptly; elapsed={elapsed:.3f}s "
        f"(limit {ABORT_ELAPSED_LIMIT_S}s); full block would be {BLOCK_BUDGET_S}s"
    )
    assert aborted.is_set(), (
        "cancel must invoke CancellationToken abort callbacks (transport close)"
    )


@pytest.mark.timeout(30)
def test_manifest_discovery_worker_cancel_aborts_transport() -> None:
    """cancel() must abort discovery listing I/O via CancellationToken callbacks."""
    _ensure_qapp()

    entered = threading.Event()
    aborted = threading.Event()

    def blocking_list_connections(cancellation_token: Any = None) -> list[Any]:
        entered.set()
        if cancellation_token is not None:
            cancellation_token.register_callback(aborted.set)
            if aborted.wait(timeout=BLOCK_BUDGET_S):
                raise OperationCancelledError("socket closed by abort")
            return []
        # Pre-fix path: no token — cancel cannot unblock this sleep.
        time.sleep(BLOCK_BUDGET_S)
        return []

    service = MagicMock()
    service.list_connections.side_effect = blocking_list_connections
    service.list_manifest_collections.return_value = []

    worker = ManifestDiscoveryWorker(
        library_service=service,
        generation_id=1,
    )
    worker.start()

    assert entered.wait(timeout=2.0), "list_connections must start before cancel"
    t0 = time.monotonic()
    worker.cancel()
    finished = worker.wait(int(ABORT_ELAPSED_LIMIT_S * 1000) + 500)
    elapsed = time.monotonic() - t0

    assert finished, "discovery worker must finish promptly after cancel"
    assert elapsed < ABORT_ELAPSED_LIMIT_S, (
        f"cancel must abort discovery transport promptly; elapsed={elapsed:.3f}s "
        f"(limit {ABORT_ELAPSED_LIMIT_S}s)"
    )
    assert aborted.is_set(), (
        "cancel must invoke CancellationToken abort callbacks for discovery I/O"
    )
