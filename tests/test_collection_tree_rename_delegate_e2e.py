"""End-to-end rename tests through QTreeView.edit and CollectionItemRenameDelegate."""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import call, patch

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

from tests.helpers.collections_tree import (
    build_isolated_tree_actions,
    cancel_inline_rename,
    commit_inline_rename,
    make_collection,
    make_request,
    patch_rename_context_menu,
    wait_for_rename_editor,
)

@pytest.mark.usefixtures("qapp")

class TestCollectionTreeRenameDelegateE2E(unittest.TestCase):
    def _prepare_harness(self, collections):
        harness = build_isolated_tree_actions(collections, with_rename_delegate=True)
        harness.view.resize(400, 300)
        harness.view.show()
        QApplication.processEvents()
        return harness

    def test_request_rename_commit_via_delegate_records_succeeded_metric(self):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        harness = self._prepare_harness([col])
        req_item = harness.model.item(0).child(0)
        with patch_rename_context_menu(harness.view, req_item.index(), action_count=3):
            harness.actions.show_context_menu(QPoint(0, 0))
        editor = wait_for_rename_editor(harness.view)
        self.assertEqual(editor.text(), "Old Name")
        commit_inline_rename(harness.view, editor, "New Name")
        harness.metrics.track_gui_collection_rename_action.assert_has_calls(
            [
                call("request", "selected"),
                call("request", "succeeded"),
            ],
            any_order=False,
        )
        self.assertIsNone(harness.actions.pending_rename)
        self.assertEqual(req.name, "New Name")
        self.assertEqual(harness.model.item(0).child(0).text(), "GET New Name")
        harness.emit_request_renamed.assert_called_once_with("r1", "New Name")

    def test_collection_rename_commit_via_delegate_records_succeeded_metric(self):
        col = make_collection("c1", "Old Collection")
        harness = self._prepare_harness([col])
        item = harness.model.item(0)
        with patch_rename_context_menu(harness.view, item.index(), action_count=2):
            harness.actions.show_context_menu(QPoint(0, 0))
        editor = wait_for_rename_editor(harness.view)
        commit_inline_rename(harness.view, editor, "New Collection")
        harness.metrics.track_gui_collection_rename_action.assert_has_calls(
            [
                call("collection", "selected"),
                call("collection", "succeeded"),
            ],
            any_order=False,
        )
        self.assertEqual(col.name, "New Collection")
        self.assertEqual(harness.model.item(0).text(), "New Collection")

    def test_request_rename_cancel_via_delegate_records_cancelled_metric(self):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        harness = self._prepare_harness([col])
        req_item = harness.model.item(0).child(0)
        with patch_rename_context_menu(harness.view, req_item.index(), action_count=3):
            harness.actions.show_context_menu(QPoint(0, 0))
        editor = wait_for_rename_editor(harness.view)
        editor.setText("Changed But Not Saved")
        cancel_inline_rename(harness.view, editor)
        harness.metrics.track_gui_collection_rename_action.assert_has_calls(
            [
                call("request", "selected"),
                call("request", "cancelled"),
            ],
            any_order=False,
        )
        self.assertIsNone(harness.actions.pending_rename)
        self.assertEqual(req.name, "Old Name")
        self.assertEqual(harness.model.item(0).child(0).text(), "GET Old Name")

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_empty_name_error")
    def test_request_rename_empty_name_via_delegate_records_rejected_empty_metric(
        self, mock_warning
    ):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        harness = self._prepare_harness([col])
        req_item = harness.model.item(0).child(0)
        with patch_rename_context_menu(harness.view, req_item.index(), action_count=3):
            harness.actions.show_context_menu(QPoint(0, 0))
        editor = wait_for_rename_editor(harness.view)
        commit_inline_rename(harness.view, editor, "   ")
        harness.metrics.track_gui_collection_rename_action.assert_has_calls(
            [
                call("request", "selected"),
                call("request", "rejected_empty"),
            ],
            any_order=False,
        )
        mock_warning.assert_called_once_with(harness.view)
        self.assertEqual(req.name, "Old Name")
        self.assertIsNone(harness.actions.pending_rename)

if __name__ == "__main__":
    unittest.main()
