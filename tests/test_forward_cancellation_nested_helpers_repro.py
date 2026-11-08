"""Failing repro test suite for PYPOST-1452 / PYPOST-1425 TD-1.

Verifies cancellation token forwarding and cooperative pre-abort through nested
connection helpers:
1. LibraryManagerService.get_connection -> list_connections
2. LibraryManagerService.list_manifest_collections -> get_connection
3. LibraryManagerService.read_manifest -> get_connection
4. LibraryManagerService.read_collection -> get_connection (nested second call)
5. LibraryCollectionImportService.list_entries -> _connections -> list_connections
6. LibraryCollectionImportService.resolve_entries -> _find_connection -> get_connection
7. Duck-typing fallback for legacy library manager test doubles without token support
8. Immediate cooperative abort on pre-cancelled tokens across all nested helpers
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.cancellation import (
    CancellationTokenSource,
    OperationCancelledError,
)
from pypost.core.library_collection_import import (
    LibraryCollectionImportEntry,
    LibraryCollectionImportService,
)
from pypost.core.library_manager_service import LibraryManagerService
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType

pytestmark = pytest.mark.timeout(10)


def _make_library_manager() -> tuple[LibraryManagerService, MagicMock, MagicMock]:
    """Create a lightweight LibraryManagerService with mock dependencies."""
    mock_store = MagicMock()
    mock_predefined = MagicMock()
    mock_predefined.diagnostics = []
    mock_overlay = MagicMock()
    manager = LibraryManagerService(
        connection_store=mock_store,
        predefined_library=mock_predefined,
        overlay_manager=mock_overlay,
    )
    return manager, mock_store, mock_predefined


def test_repro_get_connection_forwards_cancellation_token() -> None:
    """get_connection should accept and forward cancellation_token to list_connections."""
    manager, _, _ = _make_library_manager()
    cts = CancellationTokenSource()
    token = cts.token
    record = LibraryConnectionRecord(
        stable_id="lib-alpha",
        manifest_id="lib-alpha",
        display_name="Alpha Library",
        local_path=Path("/tmp/lib-alpha"),
        source_type=LibrarySourceType.REGISTERED,
    )

    with patch.object(manager, "list_connections", return_value=[record]) as mock_list:
        result = manager.get_connection("lib-alpha", cancellation_token=token)
        assert result == record
        mock_list.assert_called_once_with(cancellation_token=token)


def test_repro_list_manifest_collections_forwards_cancellation_token_to_get_connection() -> None:
    """list_manifest_collections should forward cancellation_token to get_connection."""
    manager, _, _ = _make_library_manager()
    cts = CancellationTokenSource()
    token = cts.token

    with patch.object(manager, "get_connection", return_value=None) as mock_get:
        with pytest.raises(ValueError, match="library_invalid"):
            manager.list_manifest_collections("lib-alpha", cancellation_token=token)
        mock_get.assert_called_once_with("lib-alpha", cancellation_token=token)


def test_repro_read_manifest_forwards_cancellation_token_to_get_connection() -> None:
    """read_manifest should accept and forward cancellation_token to get_connection."""
    manager, _, _ = _make_library_manager()
    cts = CancellationTokenSource()
    token = cts.token

    with patch.object(manager, "get_connection", return_value=None) as mock_get:
        with pytest.raises(ValueError, match="library_invalid"):
            manager.read_manifest("lib-alpha", cancellation_token=token)
        mock_get.assert_called_once_with("lib-alpha", cancellation_token=token)


def test_repro_read_collection_forwards_cancellation_token_to_nested_get_connection() -> None:
    """read_collection should forward cancellation_token to the nested get_connection call."""
    manager, _, _ = _make_library_manager()
    cts = CancellationTokenSource()
    token = cts.token
    record = LibraryConnectionRecord(
        stable_id="lib-alpha",
        manifest_id="lib-alpha",
        display_name="Alpha Library",
        local_path=Path("/tmp/lib-alpha"),
        source_type=LibrarySourceType.REGISTERED,
    )

    with patch.object(
        manager,
        "list_manifest_collections",
        return_value=[{"path": "collections/col1.json"}],
    ), patch.object(
        manager,
        "get_connection",
        return_value=record,
    ) as mock_get, patch(
        "pypost.core.library_manager_service.read_collection_file",
        return_value=MagicMock(),
    ):
        manager.read_collection(
            "lib-alpha",
            "collections/col1.json",
            cancellation_token=token,
        )
        mock_get.assert_called_once_with("lib-alpha", cancellation_token=token)


def test_repro_library_collection_import_list_entries_forwards_token_to_connections() -> None:
    """list_entries should forward cancellation_token to _connections and list_connections."""
    mock_manager = MagicMock()
    mock_manager.list_connections.return_value = []
    service = LibraryCollectionImportService(library_manager=mock_manager)
    cts = CancellationTokenSource()
    token = cts.token

    service.list_entries(cancellation_token=token)
    mock_manager.list_connections.assert_called_once_with(cancellation_token=token)


def test_repro_library_collection_import_resolve_entries_forwards_token_to_find_connection(
) -> None:
    """resolve_entries should forward cancellation_token to _find_connection & get_connection."""
    mock_manager = MagicMock()
    mock_manager.list_connections.return_value = []
    mock_manager.get_connection.return_value = None
    service = LibraryCollectionImportService(library_manager=mock_manager)
    cts = CancellationTokenSource()
    token = cts.token

    entry = LibraryCollectionImportEntry(
        library_id="lib-alpha",
        manifest_id="lib-alpha",
        collection_path="collections/col1.json",
        display_name="Collection 1",
        source_type=LibrarySourceType.REGISTERED,
    )

    with patch.object(service, "_find_connection", wraps=service._find_connection) as spy_find:
        service.resolve_entries([entry], cancellation_token=token)
        spy_find.assert_called_once_with("lib-alpha", cancellation_token=token)
    mock_manager.get_connection.assert_called_once_with("lib-alpha", cancellation_token=token)


def test_repro_duck_typing_fallback_for_legacy_library_manager_without_token_support() -> None:
    """Collaborator methods without cancellation_token parameter should not fail with TypeError."""
    record = LibraryConnectionRecord(
        stable_id="lib-legacy",
        manifest_id="lib-legacy",
        display_name="Legacy Library",
        local_path=Path("/tmp/lib-legacy"),
        source_type=LibrarySourceType.REGISTERED,
    )

    class _LegacyManagerDouble:
        """Collaborator double whose methods do not accept cancellation_token."""

        def list_connections(self) -> list[LibraryConnectionRecord]:
            return [record]

        def get_connection(self, stable_id: str) -> LibraryConnectionRecord | None:
            if stable_id == "lib-legacy":
                return record
            return None

    legacy_manager = _LegacyManagerDouble()
    service = LibraryCollectionImportService(library_manager=legacy_manager)
    cts = CancellationTokenSource()
    token = cts.token

    connections = service._connections(cancellation_token=token)
    assert connections == [record]

    found = service._find_connection("lib-legacy", cancellation_token=token)
    assert found == record


def test_repro_nested_helpers_abort_immediately_when_pre_cancelled() -> None:
    """Nested helpers must cooperatively abort immediately when pre-cancelled."""
    manager, mock_store, _ = _make_library_manager()
    mock_manager = MagicMock()
    service = LibraryCollectionImportService(library_manager=mock_manager)

    cts = CancellationTokenSource()
    cts.cancel("Operation cancelled prior to nested execution")

    # 1. manager.get_connection must abort immediately without querying store
    with pytest.raises(OperationCancelledError):
        manager.get_connection("lib-alpha", cancellation_token=cts.token)
    mock_store.load.assert_not_called()

    # 2. manager.read_manifest must abort immediately
    with pytest.raises(OperationCancelledError):
        manager.read_manifest("lib-alpha", cancellation_token=cts.token)

    # 3. service._connections must abort immediately without invoking collaborator
    with pytest.raises(OperationCancelledError):
        service._connections(cancellation_token=cts.token)
    mock_manager.list_connections.assert_not_called()

    # 4. service._find_connection must abort immediately without invoking collaborator
    with pytest.raises(OperationCancelledError):
        service._find_connection("lib-alpha", cancellation_token=cts.token)
    mock_manager.get_connection.assert_not_called()


def test_nested_helpers_observability_logging_on_lookup(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Connection lookup invocations must emit structured debug traces."""
    manager, _, _ = _make_library_manager()
    mock_manager = MagicMock()
    mock_manager.list_connections.return_value = []
    service = LibraryCollectionImportService(library_manager=mock_manager)

    with caplog.at_level(logging.DEBUG, logger="pypost.core.library_manager_service"):
        manager.get_connection("lib-alpha")
    assert any(
        "library_manager_get_connection_lookup stable_id=lib-alpha" in r.message
        for r in caplog.records
    )

    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="pypost.core.library_collection_import"):
        service._find_connection("lib-alpha")
    assert any(
        "library_collection_find_connection_lookup library_id=lib-alpha" in r.message
        for r in caplog.records
    )


def test_nested_helpers_observability_logging_on_cancellation(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Cooperative cancellation aborts must emit structured debug logs."""
    manager, _, _ = _make_library_manager()
    mock_manager = MagicMock()
    service = LibraryCollectionImportService(library_manager=mock_manager)

    cts = CancellationTokenSource()
    cts.cancel("Cancelled for observability verification")

    with caplog.at_level(logging.DEBUG, logger="pypost.core.library_manager_service"):
        with pytest.raises(OperationCancelledError):
            manager.get_connection("lib-alpha", cancellation_token=cts.token)
        with pytest.raises(OperationCancelledError):
            manager.list_connections(cancellation_token=cts.token)
        with pytest.raises(OperationCancelledError):
            manager.read_manifest("lib-alpha", cancellation_token=cts.token)

    messages = [r.message for r in caplog.records]
    assert any(
        "library_manager_get_connection_cancelled stable_id=lib-alpha" in m
        for m in messages
    )
    assert any("library_manager_list_connections_cancelled" in m for m in messages)
    assert any(
        "library_manager_read_manifest_cancelled stable_id=lib-alpha" in m
        for m in messages
    )

    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="pypost.core.library_collection_import"):
        with pytest.raises(OperationCancelledError):
            service._connections(cancellation_token=cts.token)
        with pytest.raises(OperationCancelledError):
            service._find_connection("lib-alpha", cancellation_token=cts.token)

    import_messages = [r.message for r in caplog.records]
    assert any("library_collection_connections_cancelled" in m for m in import_messages)
    assert any(
        "library_collection_find_connection_cancelled library_id=lib-alpha" in m
        for m in import_messages
    )
