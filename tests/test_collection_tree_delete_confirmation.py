"""Tests for delete confirmation-dialog Yes/No branching in CollectionTreeActions."""

import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, call, patch

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QMessageBox

from pypost.models.models import Collection, RequestData
from pypost.ui.presenters.collections_presenter import CollectionsPresenter


def _make_collection(col_id: str, name: str, requests=None) -> Collection:
    return Collection(id=col_id, name=name, requests=requests or [])


def _make_request(req_id: str, name: str, method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)


class FakeRequestManager:
    def __init__(self, collections=None):
        self.collections = collections or []
        self.storage = MagicMock()
        self.storage.load_collections.return_value = self.collections

    def reload_collections(self):
        self.collections = self.storage.load_collections()

    def get_collections(self):
        return self.collections

    def delete_collection_item(self, item_id, item_type):
        if item_type == "request":
            for col in self.collections:
                col.requests = [req for req in col.requests if req.id != item_id]
        elif item_type == "collection":
            self.collections = [col for col in self.collections if col.id != item_id]
        return True


class FakeStateManager:
    def get_expanded_collections(self):
        return []

    def set_expanded_collections(self, ids):
        pass


class TestCollectionTreeDeleteConfirmation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter(self, collections=None):
        rm = FakeRequestManager(collections or [])
        sm = FakeStateManager()
        metrics = MagicMock()
        return CollectionsPresenter(rm, sm, metrics, icons={}), metrics

    @contextmanager
    def _delete_via_menu(self, presenter, item_index, *, action_count):
        rename_action = MagicMock()
        delete_action = MagicMock()
        if action_count == 2:
            side_effect = [rename_action, delete_action]
        else:
            new_tab_action = MagicMock()
            side_effect = [new_tab_action, rename_action, delete_action]
        with patch.object(presenter._view, "indexAt", return_value=item_index):
            with patch("pypost.ui.presenters.collection_tree_actions.QMenu") as mock_menu_class:
                mock_menu = MagicMock()
                mock_menu.addAction.side_effect = side_effect
                mock_menu.exec.return_value = delete_action
                mock_menu_class.return_value = mock_menu
                yield delete_action

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_collection_delete_no_records_cancelled_metric(self, mock_confirm_delete):
        col = _make_collection("c1", "My API")
        presenter, metrics = self._make_presenter([col])
        presenter.load_collections()
        mock_confirm_delete.return_value = False
        item = presenter._model.item(0)
        with self._delete_via_menu(presenter, item.index(), action_count=2):
            presenter._tree_actions.show_context_menu(QPoint(0, 0))
        mock_confirm_delete.assert_called_once()
        self.assertEqual("My API", mock_confirm_delete.call_args.args[1])
        metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("collection", "selected"), call("collection", "cancelled")]
        )
        self.assertEqual(presenter._model.rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_collection_delete_yes_records_succeeded_metric(self, mock_confirm_delete):
        col = _make_collection("c1", "My API")
        presenter, metrics = self._make_presenter([col])
        presenter.load_collections()
        mock_confirm_delete.return_value = True
        item = presenter._model.item(0)
        with self._delete_via_menu(presenter, item.index(), action_count=2):
            presenter._tree_actions.show_context_menu(QPoint(0, 0))
        metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("collection", "selected"), call("collection", "succeeded")]
        )
        self.assertEqual(presenter._model.rowCount(), 0)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_request_delete_no_records_cancelled_metric(self, mock_confirm_delete):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter, metrics = self._make_presenter([col])
        presenter.load_collections()
        mock_confirm_delete.return_value = False
        req_item = presenter._model.item(0).child(0)
        with self._delete_via_menu(presenter, req_item.index(), action_count=3):
            presenter._tree_actions.show_context_menu(QPoint(0, 0))
        metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("request", "selected"), call("request", "cancelled")]
        )
        self.assertEqual(presenter._model.item(0).rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_request_delete_yes_records_succeeded_metric(self, mock_confirm_delete):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter, metrics = self._make_presenter([col])
        presenter.load_collections()
        mock_confirm_delete.return_value = True
        req_item = presenter._model.item(0).child(0)
        with self._delete_via_menu(presenter, req_item.index(), action_count=3):
            presenter._tree_actions.show_context_menu(QPoint(0, 0))
        metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("request", "selected"), call("request", "succeeded")]
        )
        self.assertEqual(presenter._model.item(0).rowCount(), 0)

    @patch(
        "pypost.ui.presenters.collection_tree_actions.CollectionTreeActions.handle_delete"
    )
    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_delete_no_skips_handle_delete(self, mock_confirm_delete, mock_handle_delete):
        col = _make_collection("c1", "My API")
        presenter, _metrics = self._make_presenter([col])
        presenter.load_collections()
        mock_confirm_delete.return_value = False
        item = presenter._model.item(0)
        with self._delete_via_menu(presenter, item.index(), action_count=2):
            presenter._tree_actions.show_context_menu(QPoint(0, 0))
        mock_handle_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
