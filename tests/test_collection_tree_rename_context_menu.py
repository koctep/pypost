"""Direct unit tests for rename context-menu dispatch in CollectionTreeActions."""

import pytest

import unittest
from unittest.mock import call, patch

from PySide6.QtCore import QPoint

from tests.helpers.collections_tree import (
    isolated_tree_actions,
    make_collection,
    make_request,
    patch_rename_context_menu,
)

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")
class TestCollectionTreeRenameContextMenu(unittest.TestCase):
    def test_collection_rename_selected_records_selected_metric(self):
        col = make_collection("c1", "My API")
        with isolated_tree_actions([col]) as harness:
            item = harness.model.item(0)
            with patch.object(harness.view, "edit") as mock_edit:
                with patch_rename_context_menu(harness.view, item.index(), action_count=3):
                    harness.actions.show_context_menu(QPoint(0, 0))
            harness.metrics.track_gui_collection_rename_action.assert_called_once_with(
                "collection", "selected"
            )
            self.assertIsNotNone(harness.actions.pending_rename)
            mock_edit.assert_called_once()

    def test_request_rename_selected_records_selected_metric(self):
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        with isolated_tree_actions([col]) as harness:
            req_item = harness.model.item(0).child(0)
            with patch.object(harness.view, "edit") as mock_edit:
                with patch_rename_context_menu(harness.view, req_item.index(), action_count=4):
                    harness.actions.show_context_menu(QPoint(0, 0))
            harness.metrics.track_gui_collection_rename_action.assert_called_once_with(
                "request", "selected"
            )
            self.assertEqual(
                harness.actions.pending_rename,
                {"item_id": "r1", "item_type": "request"},
            )
            mock_edit.assert_called_once()

    def test_collection_rename_cancel_records_cancelled_metric(self):
        col = make_collection("c1", "My API")
        with isolated_tree_actions([col]) as harness:
            harness.actions._pending_rename = {"item_id": "c1", "item_type": "collection"}
            harness.actions.handle_rename_cancelled()
            harness.metrics.track_gui_collection_rename_action.assert_called_once_with(
                "collection", "cancelled"
            )
            self.assertIsNone(harness.actions.pending_rename)
            self.assertEqual(harness.model.item(0).text(), "My API")

    def test_request_rename_cancel_records_cancelled_metric(self):
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        with isolated_tree_actions([col]) as harness:
            harness.actions._pending_rename = {"item_id": "r1", "item_type": "request"}
            harness.actions.handle_rename_cancelled()
            harness.metrics.track_gui_collection_rename_action.assert_called_once_with(
                "request", "cancelled"
            )
            self.assertIsNone(harness.actions.pending_rename)
            self.assertEqual(harness.model.item(0).child(0).text(), "GET Get users")

    def test_collection_rename_commit_records_succeeded_metric(self):
        col = make_collection("c1", "Old Collection")
        with isolated_tree_actions([col]) as harness:
            harness.actions._pending_rename = {"item_id": "c1", "item_type": "collection"}
            harness.actions.handle_rename_committed("New Collection")
            harness.metrics.track_gui_collection_rename_action.assert_called_once_with(
                "collection", "succeeded"
            )
            self.assertEqual(col.name, "New Collection")

    def test_request_rename_commit_records_succeeded_metric(self):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        with isolated_tree_actions([col]) as harness:
            harness.actions._pending_rename = {"item_id": "r1", "item_type": "request"}
            harness.actions.handle_rename_committed("New Name")
            harness.metrics.track_gui_collection_rename_action.assert_called_once_with(
                "request", "succeeded"
            )
            self.assertEqual(req.name, "New Name")

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_empty_name_error")
    def test_rename_empty_name_records_rejected_empty_metric(self, _mock_warning):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        with isolated_tree_actions([col]) as harness:
            harness.actions._pending_rename = {"item_id": "r1", "item_type": "request"}
            harness.actions.handle_rename_rejected_empty()
            harness.metrics.track_gui_collection_rename_action.assert_called_once_with(
                "request", "rejected_empty"
            )
            self.assertEqual(req.name, "Old Name")

    def test_rename_selected_does_not_emit_succeeded_metric(self):
        col = make_collection("c1", "My API")
        with isolated_tree_actions([col]) as harness:
            item = harness.model.item(0)
            with patch.object(harness.view, "edit"):
                with patch_rename_context_menu(harness.view, item.index(), action_count=3):
                    harness.actions.show_context_menu(QPoint(0, 0))
            harness.metrics.track_gui_collection_rename_action.assert_has_calls(
                [call("collection", "selected")],
                any_order=False,
            )
            self.assertNotIn(
                call("collection", "succeeded"),
                harness.metrics.track_gui_collection_rename_action.call_args_list,
            )


if __name__ == "__main__":
    unittest.main()
