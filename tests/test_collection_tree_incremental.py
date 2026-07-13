"""Tests for incremental collection tree refresh."""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest

from PySide6.QtWidgets import QApplication

from pypost.models.models import Collection, RequestData
from pypost.ui.presenters.collection_tree_incremental import try_incremental_tree_refresh
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
    make_collection,
    make_request,
)


class TestCollectionTreeIncremental(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter(self, collections=None):
        col = collections or []
        rm = FakeRequestManager(col)
        sm = FakeStateManager()
        metrics = FakeMetrics()
        return CollectionsPresenter(rm, sm, metrics, icons={})

    def test_incremental_refresh_updates_labels_without_clearing_model(self):
        req = make_request("r1", "Old Name", "GET")
        col = make_collection("c1", "Old Col", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        model_row_count_before = presenter.widget.model().rowCount()

        updated = make_collection(
            "c1",
            "New Col",
            [make_request("r1", "New Name", "POST")],
        )
        presenter._request_manager.apply_loaded_collections([updated])
        presenter.refresh_tree()

        self.assertEqual(presenter.widget.model().rowCount(), model_row_count_before)
        col_item = presenter.widget.model().item(0)
        self.assertEqual(col_item.text(), "New Col")
        self.assertEqual(col_item.child(0).text(), "POST New Name")

    def test_try_incremental_returns_false_when_collection_added(self):
        col = make_collection("c1", "Col", [])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        added = [col, make_collection("c2", "Other", [])]
        self.assertFalse(
            try_incremental_tree_refresh(presenter._collection_items_by_id, added)
        )
