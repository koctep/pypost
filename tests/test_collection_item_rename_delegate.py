"""Tests for CollectionItemRenameDelegate."""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemDelegate, QApplication, QLineEdit, QTreeView

from pypost.models.models import RequestData
from pypost.ui.delegates.collection_item_rename_delegate import CollectionItemRenameDelegate


class TestCollectionItemRenameDelegate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def _make_delegate(self):
        committed = MagicMock()
        cancelled = MagicMock()
        rejected_empty = MagicMock()
        pending = {"item_id": "r1", "item_type": "request"}

        def is_rename_index(index):
            item = index.model().itemFromIndex(index)
            data = item.data(Qt.UserRole)
            return isinstance(data, RequestData) and data.id == "r1"

        delegate = CollectionItemRenameDelegate(
            is_rename_index=is_rename_index,
            on_committed=committed,
            on_cancelled=cancelled,
            on_rejected_empty=rejected_empty,
        )
        return delegate, committed, cancelled, rejected_empty, pending

    def test_create_editor_only_for_rename_index(self):
        model = QStandardItemModel()
        req = RequestData(id="r1", name="Old", method="GET", url="http://x")
        item = QStandardItem("GET Old")
        item.setData(req, Qt.UserRole)
        model.appendRow(item)

        delegate, _, _, _, _ = self._make_delegate()
        index = model.index(0, 0)
        editor = delegate.createEditor(None, None, index)
        self.assertIsInstance(editor, QLineEdit)

        other = QStandardItem("Other")
        other.setData("c2", Qt.UserRole)
        model.appendRow(other)
        self.assertIsNone(delegate.createEditor(None, None, model.index(1, 0)))

    def test_set_editor_data_uses_request_name(self):
        model = QStandardItemModel()
        req = RequestData(id="r1", name="Request Name", method="GET", url="http://x")
        item = QStandardItem("GET Request Name")
        item.setData(req, Qt.UserRole)
        model.appendRow(item)

        delegate, _, _, _, _ = self._make_delegate()
        editor = QLineEdit()
        delegate.setEditorData(editor, model.index(0, 0))
        self.assertEqual(editor.text(), "Request Name")

    def test_set_model_data_commits_non_empty_name(self):
        model = QStandardItemModel()
        req = RequestData(id="r1", name="Old", method="GET", url="http://x")
        item = QStandardItem("GET Old")
        item.setData(req, Qt.UserRole)
        model.appendRow(item)

        delegate, committed, _, rejected_empty, _ = self._make_delegate()
        editor = QLineEdit()
        editor.setText("  New Name  ")
        delegate.setModelData(editor, model, model.index(0, 0))
        committed.assert_called_once_with("New Name")
        rejected_empty.assert_not_called()

    def test_set_model_data_rejects_empty_name(self):
        model = QStandardItemModel()
        req = RequestData(id="r1", name="Old", method="GET", url="http://x")
        item = QStandardItem("GET Old")
        item.setData(req, Qt.UserRole)
        model.appendRow(item)

        delegate, committed, _, rejected_empty, _ = self._make_delegate()
        editor = QLineEdit()
        editor.setText("   ")
        delegate.setModelData(editor, model, model.index(0, 0))
        rejected_empty.assert_called_once()
        committed.assert_not_called()
        self.assertEqual(editor.toolTip(), "Name cannot be empty.")

    def test_close_editor_revert_calls_cancelled(self):
        delegate, _, cancelled, _, _ = self._make_delegate()
        delegate._on_close_editor(
            None, QAbstractItemDelegate.EndEditHint.RevertModelCache
        )
        cancelled.assert_called_once()


if __name__ == "__main__":
    unittest.main()
