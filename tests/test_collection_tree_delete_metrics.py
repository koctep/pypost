"""Tests for delete metric emission by status and item type in handle_delete."""

import logging

import pytest

import unittest
from unittest.mock import MagicMock, call, patch

from pypost.models.models import Collection, RequestData
from pypost.ui.presenters.collections_presenter import CollectionsPresenter

pytestmark = pytest.mark.timeout(60)


def _make_collection(col_id: str, name: str, requests=None) -> Collection:
    return Collection(id=col_id, name=name, requests=requests or [])

def _make_request(req_id: str, name: str, method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)

class FakeRequestManager:
    def __init__(self, collections=None, *, delete_result=True, delete_error=None):
        self.collections = collections or []
        self.storage = MagicMock()
        self.storage.load_collections.return_value = self.collections
        self._delete_result = delete_result
        self._delete_error = delete_error

    def reload_collections(self):
        self.collections = self.storage.load_collections()

    def get_collections(self):
        return self.collections

    def delete_collection_item(self, item_id, item_type):
        if self._delete_error is not None:
            raise self._delete_error
        return self._delete_result

class FakeStateManager:
    def get_expanded_collections(self):
        return []

    def set_expanded_collections(self, ids):
        pass

@pytest.mark.usefixtures("qapp")

class TestCollectionTreeDeleteMetrics(unittest.TestCase):
    def _make_presenter(self, request_manager):
        sm = FakeStateManager()
        metrics = MagicMock()
        return CollectionsPresenter(request_manager, sm, metrics, icons={}), metrics

    @patch("pypost.ui.presenters.collection_tree_actions.show_delete_failure")
    def test_collection_delete_error_records_error_metric(self, _mock_critical):
        rm = FakeRequestManager(
            [_make_collection("c1", "My API")],
            delete_error=RuntimeError("disk full"),
        )
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        with self.assertLogs(
            "pypost.ui.presenters.collection_tree_actions",
            level=logging.ERROR,
        ) as logs:
            presenter._tree_actions.handle_delete("c1", "collection", "My API")
        self.assertTrue(
            any("collection_item_delete_failed" in r.message for r in logs.records)
        )
        metrics.track_gui_collection_delete_action.assert_called_once_with(
            "collection", "error"
        )
        self.assertEqual(presenter._model.rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.show_delete_failure")
    def test_request_delete_error_records_error_metric(self, _mock_critical):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        rm = FakeRequestManager([col], delete_error=OSError("permission denied"))
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        with self.assertLogs(
            "pypost.ui.presenters.collection_tree_actions",
            level=logging.ERROR,
        ) as logs:
            presenter._tree_actions.handle_delete("r1", "request", "Get users")
        self.assertTrue(
            any("collection_item_delete_failed" in r.message for r in logs.records)
        )
        metrics.track_gui_collection_delete_action.assert_called_once_with("request", "error")
        self.assertEqual(presenter._model.item(0).rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.show_delete_not_found")
    def test_collection_delete_not_found_records_not_found_metric(self, _mock_warning):
        rm = FakeRequestManager([_make_collection("c1", "My API")], delete_result=False)
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._tree_actions.handle_delete("c1", "collection", "My API")
        metrics.track_gui_collection_delete_action.assert_called_once_with(
            "collection", "not_found"
        )
        self.assertEqual(presenter._model.rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.show_delete_not_found")
    def test_request_delete_not_found_records_not_found_metric(self, _mock_warning):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        rm = FakeRequestManager([col], delete_result=False)
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._tree_actions.handle_delete("r1", "request", "Get users")
        metrics.track_gui_collection_delete_action.assert_called_once_with(
            "request", "not_found"
        )
        self.assertEqual(presenter._model.item(0).rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.show_delete_failure")
    def test_delete_error_does_not_emit_succeeded_metric(self, _mock_critical):
        rm = FakeRequestManager(
            [_make_collection("c1", "My API")],
            delete_error=RuntimeError("boom"),
        )
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        with self.assertLogs(
            "pypost.ui.presenters.collection_tree_actions",
            level=logging.ERROR,
        ) as logs:
            presenter._tree_actions.handle_delete("c1", "collection", "My API")
        self.assertTrue(
            any("collection_item_delete_failed" in r.message for r in logs.records)
        )
        metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("collection", "error")],
            any_order=False,
        )
        self.assertNotIn(
            call("collection", "succeeded"),
            metrics.track_gui_collection_delete_action.call_args_list,
        )

if __name__ == "__main__":
    unittest.main()
