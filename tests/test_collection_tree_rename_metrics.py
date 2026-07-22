"""Tests for rename metric emission by status and item type in handle_rename_* paths."""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, call, patch

from pypost.models.models import Collection, RequestData
from pypost.ui.presenters.collections_presenter import CollectionsPresenter

def _make_collection(col_id: str, name: str, requests=None) -> Collection:
    return Collection(id=col_id, name=name, requests=requests or [])

def _make_request(req_id: str, name: str, method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)

class FakeRequestManager:
    def __init__(self, collections=None, *, rename_result=True, rename_error=None):
        self.collections = collections or []
        self.storage = MagicMock()
        self.storage.load_collections.return_value = self.collections
        self._rename_result = rename_result
        self._rename_error = rename_error

    def reload_collections(self):
        self.collections = self.storage.load_collections()

    def get_collections(self):
        return self.collections

    def rename_collection_item(self, item_id, item_type, new_name):
        if self._rename_error is not None:
            raise self._rename_error
        if not self._rename_result:
            return False
        normalized = new_name.strip()
        if not normalized:
            return False
        if item_type == "request":
            for col in self.collections:
                for req in col.requests:
                    if req.id == item_id:
                        req.name = normalized
                        return True
        elif item_type == "collection":
            for col in self.collections:
                if col.id == item_id:
                    col.name = normalized
                    return True
        return False

class FakeStateManager:
    def get_expanded_collections(self):
        return []

    def set_expanded_collections(self, ids):
        pass

@pytest.mark.usefixtures("qapp")

class TestCollectionTreeRenameMetrics(unittest.TestCase):
    def _make_presenter(self, request_manager):
        sm = FakeStateManager()
        metrics = MagicMock()
        return CollectionsPresenter(request_manager, sm, metrics, icons={}), metrics

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_failure")
    def test_collection_rename_error_records_error_metric(self, _mock_critical):
        rm = FakeRequestManager(
            [_make_collection("c1", "My API")],
            rename_error=RuntimeError("disk full"),
        )
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "c1", "item_type": "collection"}
        presenter._tree_actions.handle_rename_committed("New API")
        metrics.track_gui_collection_rename_action.assert_called_once_with(
            "collection", "error"
        )
        self.assertEqual(presenter._model.item(0).text(), "My API")

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_failure")
    def test_request_rename_error_records_error_metric(self, _mock_critical):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        rm = FakeRequestManager([col], rename_error=OSError("permission denied"))
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        presenter._tree_actions.handle_rename_committed("New users")
        metrics.track_gui_collection_rename_action.assert_called_once_with("request", "error")
        self.assertEqual(presenter._model.item(0).child(0).text(), "GET Get users")

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_not_found")
    def test_collection_rename_not_found_records_not_found_metric(self, _mock_warning):
        rm = FakeRequestManager([_make_collection("c1", "My API")], rename_result=False)
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "c1", "item_type": "collection"}
        presenter._tree_actions.handle_rename_committed("New API")
        metrics.track_gui_collection_rename_action.assert_called_once_with(
            "collection", "not_found"
        )
        self.assertEqual(presenter._model.item(0).text(), "My API")

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_not_found")
    def test_request_rename_not_found_records_not_found_metric(self, _mock_warning):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        rm = FakeRequestManager([col], rename_result=False)
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        presenter._tree_actions.handle_rename_committed("New users")
        metrics.track_gui_collection_rename_action.assert_called_once_with(
            "request", "not_found"
        )
        self.assertEqual(presenter._model.item(0).child(0).text(), "GET Get users")

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_empty_name_error")
    def test_rename_rejected_empty_records_rejected_empty_metric(self, _mock_warning):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        rm = FakeRequestManager([col])
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        presenter._tree_actions.handle_rename_rejected_empty()
        metrics.track_gui_collection_rename_action.assert_called_once_with(
            "request", "rejected_empty"
        )

    def test_rename_cancel_records_cancelled_metric_via_presenter(self):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        rm = FakeRequestManager([col])
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        presenter._tree_actions.handle_rename_cancelled()
        metrics.track_gui_collection_rename_action.assert_called_once_with(
            "request", "cancelled"
        )

    def test_collection_rename_succeeded_records_succeeded_metric(self):
        rm = FakeRequestManager([_make_collection("c1", "My API")])
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "c1", "item_type": "collection"}
        presenter._tree_actions.handle_rename_committed("New API")
        metrics.track_gui_collection_rename_action.assert_called_once_with(
            "collection", "succeeded"
        )
        self.assertEqual(presenter._model.item(0).text(), "New API")

    def test_request_rename_succeeded_records_succeeded_metric(self):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        rm = FakeRequestManager([col])
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        presenter._tree_actions.handle_rename_committed("Fetch users")
        metrics.track_gui_collection_rename_action.assert_called_once_with(
            "request", "succeeded"
        )
        self.assertEqual(presenter._model.item(0).child(0).text(), "GET Fetch users")

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_failure")
    def test_rename_error_does_not_emit_succeeded_metric(self, _mock_critical):
        rm = FakeRequestManager(
            [_make_collection("c1", "My API")],
            rename_error=RuntimeError("boom"),
        )
        presenter, metrics = self._make_presenter(rm)
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "c1", "item_type": "collection"}
        presenter._tree_actions.handle_rename_committed("New API")
        metrics.track_gui_collection_rename_action.assert_has_calls(
            [call("collection", "error")],
            any_order=False,
        )
        self.assertNotIn(
            call("collection", "succeeded"),
            metrics.track_gui_collection_rename_action.call_args_list,
        )

if __name__ == "__main__":
    unittest.main()
