"""Failing repros for PYPOST-1279 library-backed collection import."""

from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QPushButton

from pypost.core.collection_import import plan_collection_import
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType
from pypost.models.models import Collection, RequestData
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import FakeMetrics, FakeRequestManager, FakeStateManager
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(30)


def _library_import_module():
    """Load the planned Qt-free library import boundary with a useful failure."""
    return import_module("pypost.core.library_collection_import")


def _library_fixture(
    tmp_path: Path,
) -> tuple[MagicMock, LibraryConnectionRecord, LibraryConnectionRecord]:
    root = tmp_path / "team-library"
    (root / "collections").mkdir(parents=True)
    (root / "collections" / "payments.json").write_text(
        json.dumps(
            {
                "id": "payments-source",
                "name": "Payments",
                "description": "Shared payments API",
                "requests": [
                    {
                        "id": "payment-request",
                        "name": "List payments",
                        "method": "GET",
                        "url": "https://api.example.test/payments",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "pypost-library.yaml").write_text(
        "id: team-library\n"
        "name: Team Library\n"
        "collections:\n"
        "  - collections/payments.json\n"
        "  - collections/unnamed.json\n",
        encoding="utf-8",
    )
    (root / "collections" / "unnamed.json").write_text(
        json.dumps({"requests": []}), encoding="utf-8"
    )
    record = LibraryConnectionRecord(
        stable_id="team-library",
        manifest_id="team-library",
        display_name="Team Library",
        local_path=root,
        source_type=LibrarySourceType.REGISTERED,
    )
    clone_root = tmp_path / "managed-clone"
    (clone_root / "collections").mkdir(parents=True)
    (clone_root / "collections" / "checkout.json").write_text(
        json.dumps({"id": "checkout-source", "name": "Checkout", "requests": []}),
        encoding="utf-8",
    )
    (clone_root / "pypost-library.yaml").write_text(
        "id: managed-clone\nname: Managed Clone\n"
        "collections:\n  - collections/checkout.json\n",
        encoding="utf-8",
    )
    clone_record = LibraryConnectionRecord(
        stable_id="managed-clone",
        manifest_id="managed-clone",
        display_name="Managed Clone",
        local_path=clone_root,
        source_type=LibrarySourceType.CLONED,
    )
    manager = MagicMock()
    manager.list_connections.return_value = [record, clone_record]
    return manager, record, clone_record


def test_collections_panel_exposes_distinct_file_and_library_actions(qapp):
    """The import button must expose two explicit source choices."""
    presenter = CollectionsPresenter(
        FakeRequestManager([]), FakeStateManager(), FakeMetrics(), {}
    )
    try:
        buttons = presenter.panel.findChildren(QPushButton)
        actions = presenter.panel.findChildren(QAction)
        controls = {control.text(): control for control in [*buttons, *actions]}
        labels = set(controls)
        assert "From File" in labels
        assert "From Library" in labels
        file_control = controls["From File"]
        library_control = controls["From Library"]
        with patch.object(presenter._import_actions, "import_collections_from_file") as run_file:
            (file_control.click() if isinstance(file_control, QPushButton) else file_control.trigger())
        with patch.object(
            presenter._import_actions, "import_collections_from_library"
        ) as run_library:
            (library_control.click() if isinstance(library_control, QPushButton) else library_control.trigger())
        run_file.assert_called_once()
        run_library.assert_called_once()
    finally:
        presenter.teardown()


def test_library_import_service_lists_manifest_entries_with_safe_identity(tmp_path: Path):
    """Connected libraries project their declared collection entries for selection."""
    manager, _record, _clone_record = _library_fixture(tmp_path)
    module = _library_import_module()
    service = module.LibraryCollectionImportService(library_manager=manager)

    entries = service.list_entries()

    assert len(entries) == 3
    assert {(entry.library_id, entry.collection_path) for entry in entries} == {
        ("team-library", "collections/payments.json"),
        ("team-library", "collections/unnamed.json"),
        ("managed-clone", "collections/checkout.json"),
    }
    assert {entry.display_name for entry in entries} >= {
        "Payments",
        "Checkout",
        "collections/unnamed.json",
    }
    assert any(entry.error for entry in entries if entry.collection_path.endswith("unnamed.json"))


def test_library_import_copy_and_link_modes_preserve_content_and_source_metadata(
    tmp_path: Path,
):
    """Copy is independent while Link carries an explicit source association."""
    manager, _record, _clone_record = _library_fixture(tmp_path)
    module = _library_import_module()
    service = module.LibraryCollectionImportService(library_manager=manager)
    entry = next(
        entry
        for entry in service.list_entries()
        if entry.collection_path == "collections/payments.json"
    )
    candidate = service.resolve_entries([entry]).candidates[0]
    source_files_before = {
        path: path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    connections_before = [record.model_copy(deep=True) for record in manager.list_connections.return_value]

    copied = service.materialize_candidate(candidate, module.LibraryImportMode.COPY)
    linked = service.materialize_candidate(candidate, module.LibraryImportMode.LINK)

    assert copied.library_link is None
    assert linked.library_link.library_id == "team-library"
    assert linked.library_link.collection_path == "collections/payments.json"
    assert copied.requests[0].url == linked.requests[0].url
    assert copied.requests[0] is not linked.requests[0]
    active_manager = FakeRequestManager([])
    service.apply_candidates(active_manager, [copied], module.LibraryImportMode.COPY)
    assert active_manager.get_collections()[0].library_link is None
    active_manager.storage.save_collection.assert_called_once()
    linked_manager = FakeRequestManager([])
    service.apply_candidates(linked_manager, [candidate], module.LibraryImportMode.LINK)
    assert linked_manager.get_collections()[0].library_link.library_id == "team-library"
    linked_manager.storage.save_collection.assert_called_once()
    assert manager.list_connections.call_count >= 1
    assert {
        path: path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    } == source_files_before
    assert manager.list_connections.return_value == connections_before


def test_link_refresh_reads_new_source_content_and_preserves_active_identity(tmp_path: Path):
    """A linked collection refresh is source-authoritative but ID-stable."""
    manager, record, _clone_record = _library_fixture(tmp_path)
    module = _library_import_module()
    service = module.LibraryCollectionImportService(library_manager=manager)
    entry = next(
        entry
        for entry in service.list_entries()
        if entry.collection_path == "collections/payments.json"
    )
    candidate = service.resolve_entries([entry]).candidates[0]
    linked = service.materialize_candidate(candidate, module.LibraryImportMode.LINK)
    source_path = record.local_path / "collections" / "payments.json"
    source_path.write_text(
        json.dumps(
            {
                "id": "payments-source",
                "name": "Payments",
                "requests": [{"id": "new-request", "name": "Updated", "url": "https://new.example.test"}],
            }
        ),
        encoding="utf-8",
    )

    refreshed = service.refresh_linked_collection(linked)

    assert refreshed.id == linked.id
    assert refreshed.library_link == linked.library_link
    assert refreshed.requests[0].url == "https://new.example.test"


def test_link_refresh_preserves_selected_record_in_multi_collection_file(tmp_path: Path):
    """A link to a later bundled record refreshes that record, not the first."""
    manager, record, _clone_record = _library_fixture(tmp_path)
    bundle_path = record.local_path / "collections" / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            [
                {"id": "first", "name": "First", "requests": []},
                {
                    "id": "second",
                    "name": "Second",
                    "requests": [{"id": "second-request", "url": "https://old.example.test"}],
                },
            ]
        ),
        encoding="utf-8",
    )
    (record.local_path / "pypost-library.yaml").write_text(
        "id: team-library\nname: Team Library\ncollections:\n  - collections/bundle.json\n",
        encoding="utf-8",
    )
    module = _library_import_module()
    service = module.LibraryCollectionImportService(library_manager=manager)
    entry = next(entry for entry in service.list_entries() if entry.collection_index == 1)
    linked = service.materialize_candidate(
        service.resolve_entries([entry]).candidates[0], module.LibraryImportMode.LINK
    )
    bundle_path.write_text(
        json.dumps(
            [
                {"id": "first", "name": "First", "requests": []},
                {
                    "id": "second",
                    "name": "Second Updated",
                    "requests": [{"id": "second-request", "url": "https://new.example.test"}],
                },
            ]
        ),
        encoding="utf-8",
    )

    refreshed = service.refresh_linked_collection(linked)

    assert linked.library_link.collection_index == 1
    assert refreshed.name == "Second Updated"
    assert refreshed.requests[0].url == "https://new.example.test"


def test_library_import_rejects_traversal_and_does_not_touch_source(tmp_path: Path):
    """A selected manifest path must be checked again before any active write."""
    manager, record, _clone_record = _library_fixture(tmp_path)
    module = _library_import_module()
    for invalid_path in ("../outside.json", "/tmp/outside.json", r"..\\outside.json"):
        manifest = record.local_path / "pypost-library.yaml"
        manifest.write_text(
            f"id: team-library\nname: Team Library\ncollections:\n  - {invalid_path}\n",
            encoding="utf-8",
        )
        before = manifest.read_bytes()
        connections_before = [record.model_copy(deep=True) for record in manager.list_connections.return_value]
        service = module.LibraryCollectionImportService(library_manager=manager)
        entries = [
            entry
            for entry in service.list_entries()
            if entry.library_id == "team-library"
        ]
        assert entries[0].error is not None
        active_manager = FakeRequestManager([])
        with pytest.raises(module.LibraryCollectionImportError):
            service.import_entries(
                active_manager,
                entries,
                mode=module.LibraryImportMode.LINK,
                conflict_decisions={},
            )
        assert manifest.read_bytes() == before
        assert active_manager.get_collections() == []
        assert active_manager.storage.save_collection.call_count == 0
        assert manager.list_connections.return_value == connections_before
        assert "path" in str(entries[0].error).lower() or "invalid" in str(entries[0].error).lower()


def test_library_import_rejects_source_disappearance_after_selection(tmp_path: Path):
    """A source removed after listing cannot become an empty active collection."""
    manager, _record, _clone_record = _library_fixture(tmp_path)
    module = _library_import_module()
    service = module.LibraryCollectionImportService(library_manager=manager)
    entry = next(
        entry
        for entry in service.list_entries()
        if entry.collection_path == "collections/payments.json"
    )
    (tmp_path / "team-library" / "collections" / "payments.json").unlink()
    active_manager = FakeRequestManager([])
    connections_before = [record.model_copy(deep=True) for record in manager.list_connections.return_value]

    with pytest.raises(module.LibraryCollectionImportError) as error:
        service.import_entries(
            active_manager,
            [entry],
            mode=module.LibraryImportMode.LINK,
            conflict_decisions={},
        )

    assert "unavailable" in str(error.value).lower() or "missing" in str(error.value).lower()
    assert manager.list_connections.return_value == connections_before
    assert active_manager.get_collections() == []
    active_manager.storage.save_collection.assert_not_called()


@pytest.mark.parametrize(
    "decision",
    [
        ImportConflictDecision.SKIP,
        ImportConflictDecision.KEEP_BOTH,
        ImportConflictDecision.OVERWRITE,
    ],
)
def test_library_import_reuses_explicit_conflict_decisions(
    tmp_path: Path, decision: ImportConflictDecision
):
    """Library candidates use the same explicit conflict outcomes as file imports."""
    manager, _record, _clone_record = _library_fixture(tmp_path)
    module = _library_import_module()
    service = module.LibraryCollectionImportService(library_manager=manager)
    entry = next(
        entry
        for entry in service.list_entries()
        if entry.collection_path == "collections/payments.json"
    )
    candidate = service.resolve_entries([entry]).candidates[0]
    linked = service.materialize_candidate(candidate, module.LibraryImportMode.LINK)
    existing = [Collection(id="existing", name="Payments", requests=[])]

    result = plan_collection_import(existing, [linked], {"Payments": decision})

    if decision is ImportConflictDecision.SKIP:
        assert result.skipped == ["Payments"]
        assert len(result.persisted) == 0
    elif decision is ImportConflictDecision.KEEP_BOTH:
        assert result.renamed
        assert result.persisted[0].library_link.library_id == "team-library"
    else:
        assert result.updated == ["Payments"]
        assert result.persisted[0].library_link.library_id == "team-library"


def test_library_import_cancel_and_conflict_decision_leave_manager_unchanged(qapp):
    """Cancelled source/mode/conflict dialogs must not partially apply changes."""
    manager = FakeRequestManager(
        [Collection(id="existing", name="Payments", requests=[RequestData(id="r")])]
    )
    library_service = MagicMock()
    library_service.list_entries.return_value = [SimpleNamespace(error=None)]
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        FakeMetrics(),
        {},
        library_import_service=library_service,
        library_selector=lambda _parent, _entries: None,
    )
    try:
        presenter.import_collections_from_library()
        process_until(lambda: not presenter._import_actions.is_busy(), timeout_ms=5000)
        assert [collection.id for collection in manager.get_collections()] == ["existing"]
    finally:
        presenter.teardown()


def test_library_import_emits_bounded_operation_metrics_on_selection_cancel(qapp):
    """Library import telemetry records source and user outcome only."""
    manager = FakeRequestManager([])
    library_service = MagicMock()
    library_service.list_entries.return_value = [SimpleNamespace(error=None)]
    metrics = MagicMock()
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        metrics,
        {},
        library_import_service=library_service,
        library_selector=lambda _parent, _entries: None,
    )
    try:
        presenter.import_collections_from_library()
        process_until(lambda: not presenter._import_actions.is_busy(), timeout_ms=5000)
        assert metrics.track_gui_library_operation.call_args_list == [
            (("collection_import_library", "started"), {}),
            (("collection_import_library", "rejected"), {}),
        ]
    finally:
        presenter.teardown()


def test_library_import_mode_cancel_leaves_active_collections_unchanged(qapp):
    """Cancelling the Copy/Link choice does not apply a pending selection."""
    manager = FakeRequestManager([Collection(id="existing", name="Existing")])
    before = [collection.model_copy(deep=True) for collection in manager.get_collections()]
    library_service = MagicMock()
    library_service.list_entries.return_value = [SimpleNamespace(error=None)]
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        FakeMetrics(),
        {},
        library_import_service=library_service,
        library_selector=lambda _parent, _entries: ["selected-entry"],
        library_mode_selector=lambda _parent: None,
    )
    try:
        presenter.import_collections_from_library()
        process_until(lambda: not presenter._import_actions.is_busy(), timeout_ms=5000)
        assert manager.get_collections() == before
    finally:
        presenter.teardown()


def test_library_import_conflict_cancel_leaves_active_collections_unchanged(tmp_path: Path):
    """Cancelling a library conflict prompt does not persist partial results."""
    manager, _record, _clone_record = _library_fixture(tmp_path)
    module = _library_import_module()
    service = module.LibraryCollectionImportService(library_manager=manager)
    entry = next(
        entry
        for entry in service.list_entries()
        if entry.collection_path == "collections/payments.json"
    )
    active_manager = FakeRequestManager(
        [Collection(id="existing", name="Payments", requests=[])]
    )
    before = [collection.model_copy(deep=True) for collection in active_manager.get_collections()]

    with pytest.raises(module.LibraryCollectionImportCancelled):
        service.import_entries(
            active_manager,
            [entry],
            mode=module.LibraryImportMode.LINK,
            conflict_decisions=None,
        )

    assert active_manager.get_collections() == before
    active_manager.storage.save_collection.assert_not_called()
