"""Tests for applying a planned collection import to app state (PYPOST-987)."""

import logging
from unittest.mock import MagicMock

import pytest

from pypost.core.collection_import_apply import apply_imported_collections
from pypost.models.models import Collection
from tests.helpers.collections_tree import FakeRequestManager, make_collection, make_request

pytestmark = pytest.mark.timeout(30)


def test_swaps_in_the_planned_list_and_persists_only_the_changed_subset():
    kept = make_collection("c1", "Kept")
    imported = make_collection("c2", "Imported", [make_request("r1", "Req")])
    manager = FakeRequestManager([kept])

    failures = apply_imported_collections(manager, [kept, imported], [imported])

    assert failures == []
    assert [col.id for col in manager.get_collections()] == ["c1", "c2"]
    manager.storage.save_collection.assert_called_once_with(imported)


def test_successful_multi_collection_import_does_not_reload(caplog):
    """Happy path must not call reload_collections (PYPOST-1004 NFR)."""
    a = make_collection("c1", "A")
    b = make_collection("c2", "B")
    manager = FakeRequestManager([])
    manager.reload_collections = MagicMock(wraps=manager.reload_collections)

    with caplog.at_level(logging.WARNING, logger="pypost.core.collection_import_apply"):
        failures = apply_imported_collections(manager, [a, b], [a, b])

    assert failures == []
    assert [col.id for col in manager.get_collections()] == ["c1", "c2"]
    assert manager.storage.save_collection.call_count == 2
    manager.reload_collections.assert_not_called()
    assert not any("collection_import_reconciled" in r.message for r in caplog.records)


def test_skipped_collections_are_never_written():
    kept = make_collection("c1", "Kept")
    manager = FakeRequestManager([kept])

    apply_imported_collections(manager, [kept], [])

    manager.storage.save_collection.assert_not_called()


def test_write_failure_is_reported_and_does_not_abort_remaining_writes(caplog):
    first = make_collection("c1", "Broken")
    second = make_collection("c2", "Fine")
    manager = FakeRequestManager([])
    manager.storage.save_collection.side_effect = [OSError("disk full"), None]

    with caplog.at_level(logging.WARNING, logger="pypost.core.collection_import_apply"):
        failures = apply_imported_collections(manager, [first, second], [first, second])

    assert len(failures) == 1
    assert "Broken" in failures[0]
    assert "disk full" in failures[0]
    assert manager.storage.save_collection.call_count == 2
    assert any("collection_import_save_failed" in r.message for r in caplog.records)
    assert any(
        "collection_import_reconciled failed_count=1" in r.message for r in caplog.records
    )


def test_mid_write_save_failure_reconciles_memory_to_durable_storage(caplog):
    """After a mid-loop OSError, memory must match durable storage (PYPOST-1004)."""
    prior = make_collection("c0", "Prior")
    ok = make_collection("c1", "Saved")
    broken = make_collection("c2", "Unsaved")
    durable: list[Collection] = [prior]

    def save_collection(col: Collection) -> None:
        if col.id == "c2":
            raise OSError("disk full")
        durable[:] = [c for c in durable if c.id != col.id] + [col]

    manager = FakeRequestManager([prior])
    manager.storage.save_collection.side_effect = save_collection
    # Durable load must not alias the swapped in-memory list (would hide the bug).
    manager.storage.load_collections.side_effect = lambda: list(durable)

    with caplog.at_level(logging.WARNING, logger="pypost.core.collection_import_apply"):
        failures = apply_imported_collections(
            manager, [prior, ok, broken], [ok, broken]
        )

    assert len(failures) == 1
    assert "Unsaved" in failures[0]
    assert "disk full" in failures[0]
    memory_ids = [col.id for col in manager.get_collections()]
    durable_ids = [col.id for col in durable]
    assert memory_ids == durable_ids
    assert "c2" not in memory_ids
    assert any("collection_import_save_failed" in r.message for r in caplog.records)
    assert any(
        "collection_import_reconciled failed_count=1 collection_count=2" in r.message
        for r in caplog.records
    )


def test_partial_save_failure_returns_failed_collection_ids(caplog):
    """Save failure must return a structured result with failed_ids (PYPOST-1058)."""
    first = make_collection("c1", "Saved")
    second = make_collection("c2", "Failed")
    manager = FakeRequestManager([])
    manager.storage.save_collection.side_effect = [None, OSError("disk full")]

    with caplog.at_level(logging.WARNING, logger="pypost.core.collection_import_apply"):
        result = apply_imported_collections(manager, [first, second], [first, second])

    assert hasattr(
        result, "failed_ids"
    ), "apply_imported_collections must return result with failed_ids"
    assert result.failed_ids == {"c2"}
    assert len(result.failures) == 1
    assert "Failed" in result.failures[0]
