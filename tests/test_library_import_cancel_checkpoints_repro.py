"""Qt-free unit tests for library collection import cancellation checkpoints.

Fulfills technical debt item TD-1 from PYPOST-1324 (ai-tasks/PYPOST-1324/60-tech-debt.md).
Verifies that cooperative cancellation tokens halt execution early at intermediate loop
boundaries:
1. LibraryCollectionImportService.list_entries:
   - Outer connection loop checkpoint (pre-cancelled and mid-loop)
   - Inner manifest collections loop checkpoint (mid-loop between collection paths)
2. LibraryCollectionImportService.resolve_entries:
   - Selected entries loop checkpoint (pre-cancelled and mid-loop)
3. CollectionImportActions._resolve_library_candidates:
   - Pre-resolution checkpoint (pre-cancelled before service call)
   - Materialization loop checkpoint (mid-loop between candidates)
4. Baseline uncancelled execution for all three components.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.cancellation import (
    CancellationTokenSource,
    OperationCancelledError,
)
from pypost.core.library_collection_import import (
    LibraryCollectionImportCandidate,
    LibraryCollectionImportEntry,
    LibraryCollectionImportResolution,
    LibraryCollectionImportService,
    LibraryImportMode,
)
from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.library_manifest import find_and_read_manifest
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import (
    CollectionImportActions,
)

pytestmark = pytest.mark.timeout(30)

_LibraryEnv = tuple[
    LibraryCollectionImportService, LibraryConnectionRecord, LibraryConnectionRecord
]


class _FakeLibraryManager:
    """Lightweight Qt-free in-memory library manager double."""

    def __init__(self, connections: list[LibraryConnectionRecord]) -> None:
        self.connections = list(connections)

    def list_connections(self) -> list[LibraryConnectionRecord]:
        return list(self.connections)

    def get_connection(self, library_id: str) -> LibraryConnectionRecord | None:
        for conn in self.connections:
            if conn.stable_id == library_id or conn.manifest_id == library_id:
                return conn
        return None


@pytest.fixture
def library_env(tmp_path: Path) -> _LibraryEnv:
    """Create a two-library environment with multiple manifest collections."""
    # Library 1: 2 declared collections
    root1 = tmp_path / "lib-alpha"
    (root1 / "collections").mkdir(parents=True)
    col1_path = root1 / "collections" / "orders.json"
    col1_path.write_text(
        json.dumps({"id": "orders-coll", "name": "Orders", "requests": []}),
        encoding="utf-8",
    )
    col2_path = root1 / "collections" / "inventory.json"
    col2_path.write_text(
        json.dumps({"id": "inventory-coll", "name": "Inventory", "requests": []}),
        encoding="utf-8",
    )
    (root1 / "pypost-library.yaml").write_text(
        "id: lib-alpha\n"
        "name: Alpha Library\n"
        "collections:\n"
        "  - collections/orders.json\n"
        "  - collections/inventory.json\n",
        encoding="utf-8",
    )
    rec1 = LibraryConnectionRecord(
        stable_id="lib-alpha",
        manifest_id="lib-alpha",
        display_name="Alpha Library",
        local_path=root1,
        source_type=LibrarySourceType.REGISTERED,
    )

    # Library 2: 1 declared collection
    root2 = tmp_path / "lib-beta"
    (root2 / "collections").mkdir(parents=True)
    col3_path = root2 / "collections" / "billing.json"
    col3_path.write_text(
        json.dumps({"id": "billing-coll", "name": "Billing", "requests": []}),
        encoding="utf-8",
    )
    (root2 / "pypost-library.yaml").write_text(
        "id: lib-beta\n"
        "name: Beta Library\n"
        "collections:\n"
        "  - collections/billing.json\n",
        encoding="utf-8",
    )
    rec2 = LibraryConnectionRecord(
        stable_id="lib-beta",
        manifest_id="lib-beta",
        display_name="Beta Library",
        local_path=root2,
        source_type=LibrarySourceType.CLONED,
    )

    manager = _FakeLibraryManager([rec1, rec2])
    service = LibraryCollectionImportService(library_manager=manager)
    return service, rec1, rec2


@pytest.mark.timeout(30)
def test_list_entries_cancelled_before_iteration(
    library_env: _LibraryEnv,
) -> None:
    """Pre-cancelled token halts list_entries before processing any connection."""
    service, _, _ = library_env
    cts = CancellationTokenSource()
    cts.cancel("Early exit requested before listing")

    with patch(
        "pypost.core.library_collection_import.find_and_read_manifest",
        wraps=find_and_read_manifest,
    ) as mock_find:
        with pytest.raises(OperationCancelledError):
            service.list_entries(cancellation_token=cts.token)

    mock_find.assert_not_called()


@pytest.mark.timeout(30)
def test_list_entries_cancels_between_connections(
    library_env: _LibraryEnv,
) -> None:
    """Cancellation requested during connection 1 stops before connection 2 is processed."""
    service, rec1, rec2 = library_env
    cts = CancellationTokenSource()

    def _manifest_hook(root: Path) -> tuple[object, Path]:
        if str(rec1.local_path) in str(root):
            cts.cancel("Cancel after first connection manifest")
        return find_and_read_manifest(root)

    with patch(
        "pypost.core.library_collection_import.find_and_read_manifest",
        side_effect=_manifest_hook,
    ) as mock_find:
        with pytest.raises(OperationCancelledError):
            service.list_entries(cancellation_token=cts.token)

    assert mock_find.call_count == 1
    assert str(rec2.local_path) not in str(mock_find.call_args[0][0])


@pytest.mark.timeout(30)
def test_list_entries_cancels_between_manifest_collections(
    library_env: _LibraryEnv,
) -> None:
    """Cancellation requested during first collection stops before second collection is loaded."""
    service, rec1, _ = library_env
    cts = CancellationTokenSource()

    def _load_hook(path: Path) -> tuple[list[Collection], list[str]]:
        if "orders.json" in str(path):
            cts.cancel("Cancel after first manifest collection")
        return load_collection_import_candidates(path)

    with patch(
        "pypost.core.library_collection_import.load_collection_import_candidates",
        side_effect=_load_hook,
    ) as mock_load:
        with pytest.raises(OperationCancelledError):
            service.list_entries(connection=rec1, cancellation_token=cts.token)

    assert mock_load.call_count == 1
    assert "inventory.json" not in str(mock_load.call_args[0][0])


@pytest.mark.timeout(30)
def test_resolve_entries_cancelled_before_iteration(
    library_env: _LibraryEnv,
) -> None:
    """Pre-cancelled token halts resolve_entries immediately before resolving any entry."""
    service, _, _ = library_env
    entries = service.list_entries()
    assert len(entries) >= 2

    cts = CancellationTokenSource()
    cts.cancel("Early exit requested before resolving")

    with patch(
        "pypost.core.library_collection_import.load_collection_import_candidates",
        wraps=load_collection_import_candidates,
    ) as mock_load:
        with pytest.raises(OperationCancelledError):
            service.resolve_entries(entries, cancellation_token=cts.token)

    mock_load.assert_not_called()


@pytest.mark.timeout(30)
def test_resolve_entries_cancels_between_selected_entries(
    library_env: _LibraryEnv,
) -> None:
    """Cancellation requested during entry 1 halts resolution before entry 2 is processed."""
    service, _, _ = library_env
    entries = service.list_entries()
    assert len(entries) >= 2
    selected = [entries[0], entries[1]]

    cts = CancellationTokenSource()

    def _load_hook(path: Path) -> tuple[list[Collection], list[str]]:
        cts.cancel("Cancel during first entry resolution")
        return load_collection_import_candidates(path)

    with patch(
        "pypost.core.library_collection_import.load_collection_import_candidates",
        side_effect=_load_hook,
    ) as mock_load:
        with pytest.raises(OperationCancelledError):
            service.resolve_entries(selected, cancellation_token=cts.token)

    assert mock_load.call_count == 1


@pytest.mark.timeout(30)
def test_resolve_library_candidates_pre_resolution_checkpoint() -> None:
    """Pre-cancelled token raises OperationCancelledError without calling resolve_entries."""
    mock_service = MagicMock()
    cts = CancellationTokenSource()
    cts.cancel("Pre-resolution cancellation")

    with pytest.raises(OperationCancelledError):
        CollectionImportActions._resolve_library_candidates(
            mock_service,
            [MagicMock(spec=LibraryCollectionImportEntry)],
            LibraryImportMode.COPY,
            cancellation_token=cts.token,
        )

    mock_service.resolve_entries.assert_not_called()


@pytest.mark.timeout(30)
def test_resolve_library_candidates_materialize_loop_checkpoint() -> None:
    """Cancellation between candidate materializations raises OperationCancelledError."""
    cand1 = MagicMock(spec=LibraryCollectionImportCandidate)
    cand2 = MagicMock(spec=LibraryCollectionImportCandidate)

    mock_service = MagicMock()
    mock_service.resolve_entries.return_value = LibraryCollectionImportResolution(
        candidates=[cand1, cand2],
        errors=[],
        entries=[],
    )

    cts = CancellationTokenSource()

    def _materialize_hook(candidate: object, _mode: object) -> Collection:
        if candidate is cand1:
            cts.cancel("Cancel after candidate 1 is materialized")
            return Collection(id="coll-1", name="Collection 1")
        return Collection(id="coll-2", name="Collection 2")

    mock_service.materialize_candidate.side_effect = _materialize_hook

    with pytest.raises(OperationCancelledError):
        CollectionImportActions._resolve_library_candidates(
            mock_service,
            [MagicMock(spec=LibraryCollectionImportEntry)],
            LibraryImportMode.COPY,
            cancellation_token=cts.token,
        )

    # Candidate 1 was materialized, but candidate 2 was aborted at the checkpoint
    assert mock_service.materialize_candidate.call_count == 1
    assert mock_service.materialize_candidate.call_args[0][0] is cand1


@pytest.mark.timeout(30)
def test_library_import_checkpoints_uncancelled_baseline(
    library_env: _LibraryEnv,
) -> None:
    """Uncancelled execution for list_entries, resolve_entries, and candidate materialization."""
    service, _, _ = library_env
    cts = CancellationTokenSource()

    # 1. list_entries completes and finds all 3 declared collections across the 2 libraries
    entries = service.list_entries(cancellation_token=cts.token)
    assert len(entries) == 3
    assert all(entry.error is None for entry in entries)

    # 2. resolve_entries completes for all entries with zero errors
    resolution = service.resolve_entries(entries, cancellation_token=cts.token)
    assert len(resolution.candidates) == 3
    assert len(resolution.errors) == 0

    # 3. _resolve_library_candidates completes materialization without error
    materialized, errors = CollectionImportActions._resolve_library_candidates(
        service,
        entries,
        LibraryImportMode.COPY,
        cancellation_token=cts.token,
    )
    assert len(materialized) == 3
    assert len(errors) == 0
    assert all(isinstance(c, Collection) for c in materialized)
