import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QPoint

from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.models.models import RequestData, Collection


def _make_collection(col_id: str, name: str, requests=None) -> Collection:
    return Collection(id=col_id, name=name, requests=requests or [])


def _make_request(req_id: str, name: str, method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)


class FakeRequestManager:
    def __init__(self, collections=None):
        self.collections = collections or []
        self.deleted = []
        self.renamed = []
        self.storage = MagicMock()
        self.storage.load_collections.return_value = self.collections

    def reload_collections(self):
        self.collections = self.storage.load_collections()

    def get_collections(self):
        return self.collections

    def delete_collection_item(self, item_id, item_type):
        self.deleted.append((item_id, item_type))
        if item_type == "request":
            for col in self.collections:
                col.requests = [req for req in col.requests if req.id != item_id]
        elif item_type == "collection":
            self.collections = [col for col in self.collections if col.id != item_id]
        return True

    def rename_collection_item(self, item_id, item_type, new_name):
        self.renamed.append((item_id, item_type, new_name))
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
    def __init__(self):
        self._expanded = []

    def get_expanded_collections(self):
        return list(self._expanded)

    def set_expanded_collections(self, ids):
        self._expanded = ids


class FakeMetrics:
    def track_gui_collection_delete_action(self, *args): pass
    def track_gui_collection_rename_action(self, *args): pass


class TestCollectionsPresenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter(self, collections=None):
        col = collections or []
        rm = FakeRequestManager(col)
        rm.storage.load_collections.return_value = col
        sm = FakeStateManager()
        metrics = FakeMetrics()
        return CollectionsPresenter(rm, sm, metrics, icons={})

    def test_load_collections_populates_model(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        model = presenter.widget.model()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.item(0).text(), "My API")

    def test_load_collections_includes_requests(self):
        req = _make_request("r1", "Get Users", "GET")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        model = presenter.widget.model()
        col_item = model.item(0)
        self.assertEqual(col_item.rowCount(), 1)
        self.assertIn("Get Users", col_item.child(0).text())

    def test_load_collections_empty(self):
        presenter = self._make_presenter([])
        presenter.load_collections()
        self.assertEqual(presenter.widget.model().rowCount(), 0)

    def test_refresh_tree_populates_model_without_reload(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        rm = presenter._request_manager
        rm.reload_collections = MagicMock(wraps=rm.reload_collections)

        presenter.refresh_tree()

        rm.reload_collections.assert_not_called()
        self.assertEqual(presenter.widget.model().rowCount(), 1)
        self.assertEqual(presenter.widget.model().item(0).text(), "My API")

    def test_load_collections_reloads_from_storage(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        rm = presenter._request_manager
        rm.reload_collections = MagicMock(wraps=rm.reload_collections)

        presenter.load_collections()

        rm.reload_collections.assert_called_once()

    def test_restore_tree_state_expands_known_ids(self):
        """PYPOST-388: restore_tree_state expands ids from StateManager."""
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter._state_manager._expanded = ["c1"]
        presenter.load_collections()
        presenter.restore_tree_state()
        model = presenter.widget.model()
        index = model.item(0).index()
        self.assertTrue(presenter.widget.isExpanded(index))

    def test_widget_is_tree_view(self):
        from PySide6.QtWidgets import QTreeView
        presenter = self._make_presenter()
        self.assertIsInstance(presenter.widget, QTreeView)

    def test_open_request_in_tab_signal_emitted_on_click(self):
        req = _make_request("r1", "Get Users", "GET")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()

        received = []
        presenter.open_request_in_tab.connect(received.append)

        model = presenter.widget.model()
        col_item = model.item(0)
        req_index = col_item.child(0).index()
        presenter._on_collection_clicked(req_index)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].id, "r1")

    def test_open_request_in_tab_emits_deep_copy_on_click(self):
        req = _make_request("r1", "Get Users", "GET")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()

        received = []
        presenter.open_request_in_tab.connect(received.append)

        model = presenter.widget.model()
        tree_data = model.item(0).child(0).data(Qt.UserRole)
        req_index = model.item(0).child(0).index()
        presenter._on_collection_clicked(req_index)

        self.assertEqual(len(received), 1)
        self.assertIsNot(received[0], tree_data)
        received[0].url = "https://mutated.example.com"
        self.assertNotEqual(tree_data.url, "https://mutated.example.com")

    def test_find_collection_item_finds_collection(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        item = presenter._find_collection_item("c1", "collection")
        self.assertIsNotNone(item)
        self.assertEqual(item.data(Qt.UserRole), "c1")

    def test_find_collection_item_finds_request(self):
        req = _make_request("r1", "Get Users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        item = presenter._find_collection_item("r1", "request")
        self.assertIsNotNone(item)
        data = item.data(Qt.UserRole)
        self.assertIsInstance(data, RequestData)
        self.assertEqual(data.id, "r1")

    def test_find_collection_item_returns_none_for_missing(self):
        presenter = self._make_presenter([])
        presenter.load_collections()
        self.assertIsNone(presenter._find_collection_item("missing", "collection"))

    def test_is_collection_item_true_for_collection_index(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        index = presenter.widget.model().item(0).index()
        self.assertTrue(presenter._is_collection_item(index))

    def test_is_collection_item_false_for_request_index(self):
        req = _make_request("r1", "Get Users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        index = presenter.widget.model().item(0).child(0).index()
        self.assertFalse(presenter._is_collection_item(index))

    def test_on_tree_expanded_updates_state(self):
        """PYPOST-388: expand signal adds collection id to StateManager."""
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        model = presenter.widget.model()
        index = model.item(0).index()
        presenter._on_tree_expanded(index)
        self.assertIn("c1", presenter._state_manager.get_expanded_collections())

    def test_on_tree_collapsed_updates_state(self):
        """PYPOST-388: collapse signal removes collection id from StateManager."""
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter._state_manager._expanded = ["c1"]
        presenter.load_collections()
        model = presenter.widget.model()
        index = model.item(0).index()
        presenter._on_tree_collapsed(index)
        self.assertNotIn("c1", presenter._state_manager.get_expanded_collections())

    def test_collections_changed_signal_emitted_on_delete(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        received = []
        presenter.collections_changed.connect(lambda: received.append(True))
        presenter._tree_actions.handle_delete("c1", "collection", "My API")
        self.assertEqual(len(received), 1)

    def test_delete_request_removes_tree_node_incrementally(self):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        self.assertEqual(presenter._model.item(0).rowCount(), 1)
        presenter._tree_actions.handle_delete("r1", "request", "Get users")
        self.assertEqual(presenter._model.rowCount(), 1)
        self.assertEqual(presenter._model.item(0).rowCount(), 0)

    def test_requests_deleted_signal_emitted_for_request_delete(self):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        received = []
        presenter.requests_deleted.connect(lambda ids: received.append(ids))
        presenter._tree_actions.handle_delete("r1", "request", "Get users")
        self.assertEqual(received, [["r1"]])

    def test_requests_deleted_signal_emitted_for_collection_delete(self):
        req1 = _make_request("r1", "A")
        req2 = _make_request("r2", "B")
        col = _make_collection("c1", "My API", [req1, req2])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        received = []
        presenter.requests_deleted.connect(lambda ids: received.append(list(ids)))
        presenter._tree_actions.handle_delete("c1", "collection", "My API")
        self.assertEqual(sorted(received[0]), ["r1", "r2"])

    def test_request_renamed_signal_emitted(self):
        req = _make_request("r1", "Old Name")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()

        received = []
        presenter.request_renamed.connect(lambda rid, name: received.append((rid, name)))

        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        presenter._tree_actions.handle_rename_committed("New Name")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], ("r1", "New Name"))

    def test_tree_expansion_saved_and_restored_after_reload(self):
        """PYPOST-388/PYPOST-92: expand → persist → reload → restore → UI expanded."""
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        model = presenter.widget.model()
        index = model.item(0).index()
        presenter.widget.expand(index)
        self.assertIn("c1", presenter._state_manager.get_expanded_collections())

        presenter.load_collections()
        model = presenter.widget.model()
        index = model.item(0).index()
        self.assertFalse(presenter.widget.isExpanded(index))

        presenter.restore_tree_state()
        self.assertTrue(presenter.widget.isExpanded(index))

    def test_restore_tree_state_skips_stale_saved_collection_ids(self):
        """PYPOST-389: expanded list references unknown ids; valid rows still restore."""
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter._state_manager._expanded = ["deleted-collection", "c1"]
        presenter.load_collections()
        presenter.restore_tree_state()
        model = presenter.widget.model()
        index = model.item(0).index()
        self.assertTrue(presenter.widget.isExpanded(index))
        self.assertEqual(["deleted-collection", "c1"], presenter._state_manager._expanded)

    def test_restore_tree_state_expands_only_collections_in_saved_list(self):
        """PYPOST-391: Qt tree — only ids listed in state are expanded after restore."""
        c1 = _make_collection("c1", "First")
        c2 = _make_collection("c2", "Second")
        presenter = self._make_presenter([c1, c2])
        presenter._state_manager._expanded = ["c2"]
        presenter.load_collections()
        presenter.restore_tree_state()
        model = presenter.widget.model()
        idx1 = model.item(0).index()
        idx2 = model.item(1).index()
        self.assertFalse(presenter.widget.isExpanded(idx1))
        self.assertTrue(presenter.widget.isExpanded(idx2))

    def test_restore_tree_state_expands_via_collection_index(self):
        """PYPOST-390: restore uses id index — O(expanded) not O(all collections)."""
        collections = [_make_collection(f"c{i}", f"Col {i}") for i in range(50)]
        presenter = self._make_presenter(collections)
        presenter._state_manager._expanded = ["c49", "c10"]
        presenter.load_collections()
        self.assertEqual(len(presenter._collection_items_by_id), 50)
        presenter.restore_tree_state()
        model = presenter.widget.model()
        for i in range(50):
            index = model.item(i).index()
            expected = i in (10, 49)
            self.assertEqual(presenter.widget.isExpanded(index), expected)

    def test_collection_index_updated_on_incremental_insert_and_remove(self):
        """PYPOST-390: collection id index stays in sync with incremental tree edits."""
        presenter = self._make_presenter([])
        presenter.load_collections()
        col = _make_collection("c-new", "New")
        presenter._insert_collection_into_tree(col)
        self.assertIn("c-new", presenter._collection_items_by_id)
        presenter.remove_item_from_tree("c-new", "collection")
        self.assertNotIn("c-new", presenter._collection_items_by_id)

    @patch(
        "pypost.ui.presenters.collection_tree_actions.CollectionTreeActions.handle_delete"
    )
    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_delete_confirmation_cancelled_skips_delete(
        self, mock_confirm_delete, mock_handle_delete
    ):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        mock_confirm_delete.return_value = False
        item = presenter._model.item(0)
        with patch.object(presenter._view, "indexAt", return_value=item.index()):
            with patch("pypost.ui.presenters.collection_tree_actions.QMenu") as mock_menu_class:
                mock_menu = MagicMock()
                rename_action = MagicMock()
                delete_action = MagicMock()
                mock_menu.addAction.side_effect = [rename_action, delete_action]
                mock_menu.exec.return_value = delete_action
                mock_menu_class.return_value = mock_menu
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        mock_handle_delete.assert_not_called()

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_delete_confirmation_accepted_updates_tree(self, mock_confirm_delete):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        mock_confirm_delete.return_value = True
        req_item = presenter._model.item(0).child(0)
        with patch.object(presenter._view, "indexAt", return_value=req_item.index()):
            with patch("pypost.ui.presenters.collection_tree_actions.QMenu") as mock_menu_class:
                mock_menu = MagicMock()
                new_tab_action = MagicMock()
                rename_action = MagicMock()
                delete_action = MagicMock()
                mock_menu.addAction.side_effect = [
                    new_tab_action,
                    rename_action,
                    delete_action,
                ]
                mock_menu.exec.return_value = delete_action
                mock_menu_class.return_value = mock_menu
                presenter._tree_actions.show_context_menu(QPoint(0, 0))
        self.assertEqual(presenter._model.item(0).rowCount(), 0)

    def test_rename_cancel_restores_tree_incrementally(self):
        req = _make_request("r1", "Old Name")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        with patch.object(presenter, "refresh_tree") as mock_refresh:
            presenter._tree_actions.handle_rename_cancelled()
        self.assertIsNone(presenter._pending_rename)
        self.assertEqual(presenter._model.item(0).child(0).text(), "GET Old Name")
        mock_refresh.assert_not_called()

    def test_rename_success_updates_tree_incrementally(self):
        req = _make_request("r1", "Old Name")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        with patch.object(presenter, "refresh_tree") as mock_refresh:
            presenter._tree_actions.handle_rename_committed("New Name")
        self.assertEqual(presenter._model.item(0).child(0).text(), "GET New Name")
        self.assertEqual(req.name, "New Name")
        mock_refresh.assert_not_called()

    def test_rename_collection_success_updates_tree_incrementally(self):
        col = _make_collection("c1", "Old Collection")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "c1", "item_type": "collection"}
        with patch.object(presenter, "refresh_tree") as mock_refresh:
            presenter._tree_actions.handle_rename_committed("New Collection")
        self.assertEqual(presenter._model.item(0).text(), "New Collection")
        self.assertEqual(col.name, "New Collection")
        mock_refresh.assert_not_called()

    def test_add_saved_request_to_tree_existing_collection(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        new_req = _make_request("r2", "New Request", "POST")
        col.requests.append(new_req)

        with patch.object(presenter, "refresh_tree") as mock_refresh:
            added = presenter.add_saved_request_to_tree(new_req, "c1")

        self.assertTrue(added)
        self.assertEqual(presenter._model.item(0).rowCount(), 1)
        self.assertIn("New Request", presenter._model.item(0).child(0).text())
        mock_refresh.assert_not_called()

    def test_add_saved_request_to_tree_new_collection(self):
        presenter = self._make_presenter([])
        presenter.load_collections()
        new_req = _make_request("r1", "First Request")
        new_col = _make_collection("c-new", "New Collection", [new_req])
        presenter._request_manager.collections = [new_col]

        with patch.object(presenter, "refresh_tree") as mock_refresh:
            added = presenter.add_saved_request_to_tree(new_req, "c-new")

        self.assertTrue(added)
        self.assertEqual(presenter._model.rowCount(), 1)
        self.assertEqual(presenter._model.item(0).text(), "New Collection")
        self.assertEqual(presenter._model.item(0).rowCount(), 1)
        mock_refresh.assert_not_called()

    def test_add_saved_request_to_tree_expands_saved_collection(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter._state_manager._expanded = ["c1"]
        presenter.load_collections()
        new_req = _make_request("r2", "Expanded Request")
        col.requests.append(new_req)

        presenter.add_saved_request_to_tree(new_req, "c1")

        index = presenter._model.item(0).index()
        self.assertTrue(presenter.widget.isExpanded(index))

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_empty_name_error")
    def test_rename_empty_name_shows_warning(self, mock_warning):
        req = _make_request("r1", "Old Name")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()
        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        presenter._tree_actions.handle_rename_rejected_empty()
        mock_warning.assert_called_once()
        self.assertEqual("Old Name", req.name)


if __name__ == "__main__":
    unittest.main()
