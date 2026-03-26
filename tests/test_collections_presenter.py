import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

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
        return True

    def rename_collection_item(self, item_id, item_type, new_name):
        self.renamed.append((item_id, item_type, new_name))
        return True


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

    def test_restore_tree_state_expands_known_ids(self):
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

    def test_on_tree_expanded_updates_state(self):
        col = _make_collection("c1", "My API")
        presenter = self._make_presenter([col])
        presenter.load_collections()
        model = presenter.widget.model()
        index = model.item(0).index()
        presenter._on_tree_expanded(index)
        self.assertIn("c1", presenter._state_manager.get_expanded_collections())

    def test_on_tree_collapsed_updates_state(self):
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
        presenter._handle_delete("c1", "collection", "My API")
        self.assertEqual(len(received), 1)

    def test_request_renamed_signal_emitted(self):
        req = _make_request("r1", "Old Name")
        col = _make_collection("c1", "My API", [req])
        presenter = self._make_presenter([col])
        presenter.load_collections()

        received = []
        presenter.request_renamed.connect(lambda rid, name: received.append((rid, name)))

        item = presenter._find_collection_item("r1", "request")
        item.setEditable(True)
        item.setText("New Name")

        presenter._pending_rename = {"item_id": "r1", "item_type": "request"}
        from PySide6.QtWidgets import QAbstractItemDelegate
        presenter._on_editor_closed(None, QAbstractItemDelegate.EndEditHint.SubmitModelCache)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], ("r1", "New Name"))

    def test_tree_expansion_saved_and_restored_after_reload(self):
        """PYPOST-92: expand → persisted → load_collections → restore → UI expanded."""
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
        """PYPOST-93: expanded list references unknown ids; valid rows still restore."""
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
        """PYPOST-95: Qt tree — only ids listed in state are expanded after restore."""
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


if __name__ == "__main__":
    unittest.main()
