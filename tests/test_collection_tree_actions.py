"""GUI tests for collection tree right-click context menu behavior."""

import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint, QModelIndex
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

    def rename_collection_item(self, item_id, item_type, new_name):
        return True


class FakeStateManager:
    def get_expanded_collections(self):
        return []

    def set_expanded_collections(self, ids):
        pass


class TestCollectionTreeContextMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter(self, collections=None):
        col = collections or []
        rm = FakeRequestManager(col)
        sm = FakeStateManager()
        metrics = MagicMock()
        return CollectionsPresenter(rm, sm, metrics, icons={})

    @contextmanager
    def _patch_menu(self, actions, selected):
        with patch("pypost.ui.presenters.collection_tree_actions.QMenu") as mock_menu_class:
            mock_menu = MagicMock()
            mock_menu.addAction.side_effect = list(actions)
            mock_menu.exec.return_value = selected
            mock_menu_class.return_value = mock_menu
            yield mock_menu

    def test_invalid_index_skips_context_menu(self):
        presenter = self._make_presenter([_make_collection("c1", "My API")])
        presenter.load_collections()
        invalid = QModelIndex()
        with patch.object(presenter._view, "indexAt", return_value=invalid):
            with patch("pypost.ui.presenters.collection_tree_actions.QMenu") as mock_menu_class:
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        mock_menu_class.assert_not_called()

    def test_collection_menu_offers_rename_and_delete(self):
        presenter = self._make_presenter([_make_collection("c1", "My API")])
        presenter.load_collections()
        item = presenter._model.item(0)
        with patch.object(presenter._view, "indexAt", return_value=item.index()):
            with self._patch_menu([MagicMock(), MagicMock()], None) as mock_menu:
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        self.assertEqual(mock_menu.addAction.call_count, 2)
        labels = [call.args[0] for call in mock_menu.addAction.call_args_list]
        self.assertEqual(labels, ["Rename", "Delete"])

    def test_request_menu_offers_new_tab_rename_delete(self):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        req_item = presenter._model.item(0).child(0)
        with patch.object(presenter._view, "indexAt", return_value=req_item.index()):
            with self._patch_menu([MagicMock(), MagicMock(), MagicMock()], None) as mock_menu:
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        labels = [call.args[0] for call in mock_menu.addAction.call_args_list]
        self.assertEqual(labels, ["New tab", "Rename", "Delete"])

    def test_rename_selected_starts_inline_edit(self):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        req_item = presenter._model.item(0).child(0)
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch.object(presenter._view, "indexAt", return_value=req_item.index()):
            with patch.object(presenter._view, "edit") as mock_edit:
                with self._patch_menu(
                    [MagicMock(), rename_action, delete_action], rename_action
                ):
                    presenter._tree_actions.show_context_menu(QPoint(0, 0))
        self.assertIsNotNone(presenter._tree_actions.pending_rename)
        mock_edit.assert_called_once()

    @patch("pypost.ui.presenters.collection_tree_actions.copy_request_for_isolated_tab")
    def test_new_tab_selected_emits_open_isolated_tab(self, mock_copy):
        req = _make_request("r1", "Get users")
        copied = _make_request("r1-copy", "Get users")
        mock_copy.return_value = copied
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        emitted = []
        presenter.open_request_in_isolated_tab.connect(lambda data: emitted.append(data))
        req_item = presenter._model.item(0).child(0)
        new_tab_action = MagicMock()
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch.object(presenter._view, "indexAt", return_value=req_item.index()):
            with self._patch_menu(
                [new_tab_action, rename_action, delete_action], new_tab_action
            ):
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        mock_copy.assert_called_once_with(req)
        self.assertEqual(emitted, [copied])

    @patch("pypost.ui.presenters.collection_tree_actions.QMessageBox.question")
    def test_delete_cancelled_skips_persistence(self, mock_question):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        mock_question.return_value = QMessageBox.No
        item = presenter._model.item(0)
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch.object(presenter._view, "indexAt", return_value=item.index()):
            with self._patch_menu([rename_action, delete_action], delete_action):
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        self.assertEqual(presenter._model.rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.QMessageBox.question")
    def test_delete_confirmed_removes_request(self, mock_question):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        mock_question.return_value = QMessageBox.Yes
        req_item = presenter._model.item(0).child(0)
        new_tab_action = MagicMock()
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch.object(presenter._view, "indexAt", return_value=req_item.index()):
            with self._patch_menu(
                [new_tab_action, rename_action, delete_action], delete_action
            ):
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        self.assertEqual(presenter._model.item(0).rowCount(), 0)


if __name__ == "__main__":
    unittest.main()
