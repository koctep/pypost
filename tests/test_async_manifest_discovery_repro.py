"""Failing repro for PYPOST-1424: async library connection/manifest discovery on dialog open.

Desired behavior:
- ImportCollectionVariablesDialog __init__ must not block on slow
  library_service.list_connections() / list_manifest_collections().
- Workspace collections appear in the combo immediately.
- Remote library entries are discovered on a background worker and appended later.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QThread

from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment
from pypost.ui.dialogs.import_collection_variables_dialog import (
    ImportCollectionVariablesDialog,
)

pytestmark = [pytest.mark.timeout(30)]


def _wait_until(predicate: Any, qapp: Any, timeout_s: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        qapp.processEvents()
        time.sleep(0.02)
    return predicate()


@pytest.mark.timeout(30)
def test_dialog_init_does_not_block_on_slow_manifest_discovery(qapp: Any) -> None:
    """Dialog construction must return before slow list_connections finishes."""
    env = Environment(name="Dev", variables={})
    local = Collection(
        name="LocalCol",
        variables=[
            CollectionVariable(name="local_key", type="string", default="local_val"),
        ],
    )

    mock_service = MagicMock()
    conn_mock = MagicMock()
    conn_mock.stable_id = "conn_1"
    conn_mock.name = "Remote Conn"

    def slow_list_connections() -> list[Any]:
        time.sleep(0.2)
        return [conn_mock]

    mock_service.list_connections.side_effect = slow_list_connections
    mock_service.list_manifest_collections.return_value = [
        {"name": "RemoteCol", "path": "cols/remote.json"},
    ]

    started = time.monotonic()
    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[local],
        library_service=mock_service,
    )
    elapsed = time.monotonic() - started

    try:
        # Construction must not wait for the 200ms list_connections sleep.
        assert elapsed < 0.1, (
            f"Dialog __init__ blocked for {elapsed:.3f}s; "
            "list_connections/list_manifest_collections must run off the UI thread"
        )

        # Workspace source available immediately.
        assert dialog.collection_combo.count() >= 1
        assert dialog.collection_combo.itemText(0).startswith("LocalCol")

        # Background discovery worker must be present and running (or already finished
        # only after a short event-loop flush — not during sync __init__).
        worker = getattr(dialog, "_active_discovery_worker", None)
        assert worker is not None, (
            "Dialog must track _active_discovery_worker (ManifestDiscoveryWorker)"
        )
        assert isinstance(worker, QThread), (
            "Discovery worker must be a QThread subclass"
        )

        # Remote entry appears only after async discovery completes.
        assert _wait_until(
            lambda: any(
                "RemoteCol" in dialog.collection_combo.itemText(i)
                for i in range(dialog.collection_combo.count())
            ),
            qapp,
            timeout_s=5.0,
        ), "Remote library collections must appear after background discovery"
    finally:
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
            worker.wait(1000)
        fetch = getattr(dialog, "_active_fetch_worker", None)
        if fetch is not None:
            fetch.cancel()
            fetch.wait(1000)
        dialog.close()
