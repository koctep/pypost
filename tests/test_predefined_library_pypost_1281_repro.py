"""Red repros for the predefined examples library (PYPOST-1281)."""
from __future__ import annotations

from pathlib import Path

import pytest

from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.models.library_manager import LibrarySourceType
from pypost.ui.presenters.library_presenter import LibraryPresenter
from pypost.ui.widgets.library_manager_panel import LibraryListWidget

pytestmark = pytest.mark.timeout(30)


_EXAMPLES = Path("examples")


def _service(tmp_path: Path, root: Path = _EXAMPLES) -> LibraryManagerService:
    """Build an isolated manager with the bundled root under test."""
    return LibraryManagerService(
        connection_store=LibraryConnectionStore(tmp_path / "connections.json"),
        predefined_root=root,
    )


def test_bundled_examples_are_discovered_as_read_only_library(tmp_path: Path):
    """The official examples are available without a persisted registration."""
    service = _service(tmp_path)

    records = service.list_connections()

    predefined = next(record for record in records if record.stable_id == "pypost-examples")
    assert predefined.source_type == LibrarySourceType.PREDEFINED
    assert predefined.is_read_only is True
    assert predefined.manifest_id == "pypost-examples"
    assert predefined.local_path == _EXAMPLES


def test_predefined_library_lists_valid_manifest_collections(tmp_path: Path):
    """Only manifest-declared, readable example collections are exposed."""
    service = _service(tmp_path)

    entries = service.list_manifest_collections("pypost-examples")

    assert [entry["path"] for entry in entries] == [
        "collections/jira_mcp.json",
        "collections/mcp.json",
    ]
    assert all(entry["library_id"] == "pypost-examples" for entry in entries)


def test_predefined_copy_is_editable_and_does_not_change_bundled_source(tmp_path: Path):
    """Copying creates an independent registered library and protects the template."""
    service = _service(tmp_path)
    destination = tmp_path / "editable-examples"
    source_collection = (_EXAMPLES / "collections" / "mcp.json").read_bytes()

    record = service.copy_predefined_library(destination)

    assert record.stable_id == "pypost-examples-copy"
    assert record.source_type == LibrarySourceType.REGISTERED
    assert record.is_read_only is False
    assert (destination / "pypost-library.yaml").read_bytes() == (
        _EXAMPLES / "pypost-library.yaml"
    ).read_bytes()
    assert record.local_path != _EXAMPLES
    (destination / "collections" / "mcp.json").write_text("changed", encoding="utf-8")
    assert (destination / "collections" / "mcp.json").read_text(encoding="utf-8") == "changed"
    assert (_EXAMPLES / "collections" / "mcp.json").read_bytes() == source_collection


def test_invalid_predefined_root_is_reported_without_library_entry(tmp_path: Path):
    """A broken bundled root never becomes a misleading usable library."""
    invalid_root = tmp_path / "invalid-examples"
    invalid_root.mkdir()
    service = _service(tmp_path, invalid_root)

    records = service.list_connections()

    assert all(record.stable_id != "pypost-examples" for record in records)
    assert any("predefined" in diagnostic.lower() for diagnostic in service.diagnostics)


def test_library_manager_presents_predefined_row(qapp: object, tmp_path: Path):
    """The existing Library Manager presenter exposes the template row."""
    presenter = LibraryPresenter(service=_service(tmp_path))

    presenter.load_libraries()

    row = next(entry for entry in presenter.list_entries() if entry.stable_id == "pypost-examples")
    assert row.connection.source_type == LibrarySourceType.PREDEFINED
    assert row.connection.is_read_only is True


def test_predefined_row_exposes_only_safe_manager_actions(qapp: object, tmp_path: Path):
    """The template cannot be pulled, deleted, or disconnected in place."""
    presenter = LibraryPresenter(service=_service(tmp_path))
    presenter.load_libraries()
    widget = LibraryListWidget()
    widget.set_entries(presenter.list_entries())

    assert widget.actions_for_library("pypost-examples") == [
        "refresh",
        "copy_path",
        "copy_to_editable",
    ]
