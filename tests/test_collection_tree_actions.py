"""Direct unit tests for CollectionTreeActions (menu dispatch, rename flows)."""

import logging
import unittest
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QModelIndex, QPoint

from pypost.core.collection_messages import BUTTON_EXPORT_COLLECTION
from tests.helpers.collections_tree import (
    build_isolated_tree_actions,
    close_isolated_tree_actions,
    make_collection,
    make_request,
    patch_view_context_menu,
)

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")
class TestCollectionTreeActionsIsolated(unittest.TestCase):
    def test_invalid_index_skips_context_menu(self):
        harness = build_isolated_tree_actions([make_collection("c1", "My API")])
        self.addCleanup(close_isolated_tree_actions, harness)
        invalid = QModelIndex()
        with patch.object(harness.view, "indexAt", return_value=invalid):
            with patch("pypost.ui.presenters.collection_tree_actions.QMenu") as mock_menu_class:
                harness.actions.show_context_menu(QPoint(0, 0))
        mock_menu_class.assert_not_called()

    def test_collection_menu_offers_export_collection(self):
        """PYPOST-1013: collection row menu offers Export Collection…, Rename, Delete."""
        harness = build_isolated_tree_actions([make_collection("c1", "My API")])
        self.addCleanup(close_isolated_tree_actions, harness)
        item = harness.model.item(0)
        with patch_view_context_menu(
            harness.view,
            item.index(),
            [MagicMock(), MagicMock(), MagicMock()],
            None,
        ) as mock_menu:
            harness.actions.show_context_menu(QPoint(0, 0))
        self.assertEqual(mock_menu.addAction.call_count, 3)
        labels = [call.args[0] for call in mock_menu.addAction.call_args_list]
        self.assertEqual(labels, [BUTTON_EXPORT_COLLECTION, "Rename", "Delete"])

    def test_request_menu_offers_export_collection(self):
        """PYPOST-1013: request row menu offers New tab, Export Collection…, Rename, Delete."""
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        req_item = harness.model.item(0).child(0)
        with patch_view_context_menu(
            harness.view,
            req_item.index(),
            [MagicMock(), MagicMock(), MagicMock(), MagicMock()],
            None,
        ) as mock_menu:
            harness.actions.show_context_menu(QPoint(0, 0))
        labels = [call.args[0] for call in mock_menu.addAction.call_args_list]
        self.assertEqual(
            labels,
            ["New tab", BUTTON_EXPORT_COLLECTION, "Rename", "Delete"],
        )

    def test_collection_export_menu_dispatches_clicked_index(self):
        """PYPOST-1013: choosing Export Collection… passes the clicked index."""
        harness = build_isolated_tree_actions([make_collection("c1", "My API")])
        self.addCleanup(close_isolated_tree_actions, harness)
        item = harness.model.item(0)
        export_action = MagicMock()
        with patch_view_context_menu(
            harness.view,
            item.index(),
            [export_action, MagicMock(), MagicMock()],
            export_action,
        ):
            harness.actions.show_context_menu(QPoint(0, 0))
        harness.export_collection.assert_called_once()
        self.assertEqual(
            harness.export_collection.call_args.args[0],
            item.index(),
        )

    def test_request_export_menu_dispatches_clicked_index(self):
        """PYPOST-1013: request-row Export Collection… passes the clicked index."""
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        req_item = harness.model.item(0).child(0)
        export_action = MagicMock()
        with patch_view_context_menu(
            harness.view,
            req_item.index(),
            [MagicMock(), export_action, MagicMock(), MagicMock()],
            export_action,
        ):
            harness.actions.show_context_menu(QPoint(0, 0))
        harness.export_collection.assert_called_once()
        self.assertEqual(
            harness.export_collection.call_args.args[0],
            req_item.index(),
        )

    def test_collection_export_menu_logs_selected(self):
        """PYPOST-1013: menu Export logs collection_export_selected before dispatch."""
        harness = build_isolated_tree_actions([make_collection("c1", "My API")])
        self.addCleanup(close_isolated_tree_actions, harness)
        item = harness.model.item(0)
        export_action = MagicMock()
        with self.assertLogs(
            "pypost.ui.presenters.collection_tree_actions",
            level=logging.INFO,
        ) as captured:
            with patch_view_context_menu(
                harness.view,
                item.index(),
                [export_action, MagicMock(), MagicMock()],
                export_action,
            ):
                harness.actions.show_context_menu(QPoint(0, 0))
        self.assertTrue(
            any(
                "collection_export_selected item_type=collection item_id=c1"
                in message
                for message in captured.output
            )
        )
        harness.export_collection.assert_called_once()

    def test_rename_selected_starts_inline_edit(self):
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        req_item = harness.model.item(0).child(0)
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch.object(harness.view, "edit") as mock_edit:
            with patch_view_context_menu(
                harness.view,
                req_item.index(),
                [MagicMock(), MagicMock(), rename_action, delete_action],
                rename_action,
            ):
                harness.actions.show_context_menu(QPoint(0, 0))
        self.assertIsNotNone(harness.actions.pending_rename)
        mock_edit.assert_called_once()

    @patch("pypost.ui.presenters.collection_tree_actions.copy_request_for_isolated_tab")
    def test_new_tab_selected_emits_open_isolated_tab(self, mock_copy):
        req = make_request("r1", "Get users")
        copied = make_request("r1-copy", "Get users")
        mock_copy.return_value = copied
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        req_item = harness.model.item(0).child(0)
        new_tab_action = MagicMock()
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch_view_context_menu(
            harness.view,
            req_item.index(),
            [new_tab_action, MagicMock(), rename_action, delete_action],
            new_tab_action,
        ):
            harness.actions.show_context_menu(QPoint(0, 0))
        mock_copy.assert_called_once_with(req)
        harness.emit_open_isolated_tab.assert_called_once_with(copied)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_delete_cancelled_skips_persistence(self, mock_confirm_delete):
        harness = build_isolated_tree_actions([make_collection("c1", "My API")])
        self.addCleanup(close_isolated_tree_actions, harness)
        mock_confirm_delete.return_value = False
        item = harness.model.item(0)
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch_view_context_menu(
            harness.view,
            item.index(),
            [MagicMock(), rename_action, delete_action],
            delete_action,
        ):
            harness.actions.show_context_menu(QPoint(0, 0))
        self.assertEqual(harness.model.rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_delete_confirmed_removes_request(self, mock_confirm_delete):
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        mock_confirm_delete.return_value = True
        req_item = harness.model.item(0).child(0)
        new_tab_action = MagicMock()
        rename_action = MagicMock()
        delete_action = MagicMock()
        with patch_view_context_menu(
            harness.view,
            req_item.index(),
            [new_tab_action, MagicMock(), rename_action, delete_action],
            delete_action,
        ):
            harness.actions.show_context_menu(QPoint(0, 0))
        self.assertEqual(harness.model.item(0).rowCount(), 0)

    def test_rename_cancel_restores_tree_incrementally(self):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        harness.actions._pending_rename = {"item_id": "r1", "item_type": "request"}
        harness.actions.handle_rename_cancelled()
        self.assertIsNone(harness.actions.pending_rename)
        self.assertEqual(harness.model.item(0).child(0).text(), "GET Old Name")
        harness.refresh_tree.assert_not_called()

    def test_rename_commit_updates_request_tree_and_emits(self):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        harness.actions._pending_rename = {"item_id": "r1", "item_type": "request"}
        harness.actions.handle_rename_committed("New Name")
        self.assertEqual(harness.model.item(0).child(0).text(), "GET New Name")
        self.assertEqual(req.name, "New Name")
        harness.emit_request_renamed.assert_called_once_with("r1", "New Name")
        harness.emit_collections_changed.assert_called_once()
        harness.refresh_tree.assert_not_called()

    def test_rename_commit_updates_collection_tree(self):
        col = make_collection("c1", "Old Collection")
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        harness.actions._pending_rename = {"item_id": "c1", "item_type": "collection"}
        harness.actions.handle_rename_committed("New Collection")
        self.assertEqual(harness.model.item(0).text(), "New Collection")
        self.assertEqual(col.name, "New Collection")
        harness.emit_request_renamed.assert_not_called()
        harness.emit_collections_changed.assert_called_once()

    @patch("pypost.ui.presenters.collection_tree_actions.show_rename_empty_name_error")
    def test_rename_rejected_empty_shows_warning(self, mock_warning):
        req = make_request("r1", "Old Name")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        self.addCleanup(close_isolated_tree_actions, harness)
        harness.actions._pending_rename = {"item_id": "r1", "item_type": "request"}
        harness.actions.handle_rename_rejected_empty()
        mock_warning.assert_called_once_with(harness.view)
        self.assertEqual(req.name, "Old Name")
        self.assertIsNone(harness.actions.pending_rename)

if __name__ == "__main__":
    unittest.main()
