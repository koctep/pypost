"""Tests for applying a planned collection import to app state (PYPOST-987)."""

import logging

import pytest

from pypost.core.collection_import_apply import apply_imported_collections
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

    with caplog.at_level(logging.ERROR, logger="pypost.core.collection_import_apply"):
        failures = apply_imported_collections(manager, [first, second], [first, second])

    assert len(failures) == 1
    assert "Broken" in failures[0]
    assert "disk full" in failures[0]
    assert manager.storage.save_collection.call_count == 2
    assert any("collection_import_save_failed" in r.message for r in caplog.records)
