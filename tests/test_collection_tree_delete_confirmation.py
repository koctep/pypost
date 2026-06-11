"""Direct unit tests for delete confirmation branching in CollectionTreeActions."""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, call, patch

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

from tests.helpers.collections_tree import (
    build_isolated_tree_actions,
    make_collection,
    make_request,
    patch_delete_context_menu,
)


class TestCollectionTreeDeleteConfirmation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_collection_delete_no_records_cancelled_metric(self, mock_confirm_delete):
        col = make_collection("c1", "My API")
        harness = build_isolated_tree_actions([col])
        mock_confirm_delete.return_value = False
        item = harness.model.item(0)
        with patch_delete_context_menu(harness.view, item.index(), action_count=2):
            harness.actions.show_context_menu(QPoint(0, 0))
        mock_confirm_delete.assert_called_once()
        self.assertEqual("My API", mock_confirm_delete.call_args.args[1])
        harness.metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("collection", "selected"), call("collection", "cancelled")]
        )
        self.assertEqual(harness.model.rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_collection_delete_yes_records_succeeded_metric(self, mock_confirm_delete):
        col = make_collection("c1", "My API")
        harness = build_isolated_tree_actions([col])
        mock_confirm_delete.return_value = True
        item = harness.model.item(0)
        with patch_delete_context_menu(harness.view, item.index(), action_count=2):
            harness.actions.show_context_menu(QPoint(0, 0))
        harness.metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("collection", "selected"), call("collection", "succeeded")]
        )
        self.assertEqual(harness.model.rowCount(), 0)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_request_delete_no_records_cancelled_metric(self, mock_confirm_delete):
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        mock_confirm_delete.return_value = False
        req_item = harness.model.item(0).child(0)
        with patch_delete_context_menu(harness.view, req_item.index(), action_count=3):
            harness.actions.show_context_menu(QPoint(0, 0))
        harness.metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("request", "selected"), call("request", "cancelled")]
        )
        self.assertEqual(harness.model.item(0).rowCount(), 1)

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_request_delete_yes_records_succeeded_metric(self, mock_confirm_delete):
        req = make_request("r1", "Get users")
        col = make_collection("c1", "My API", [req])
        harness = build_isolated_tree_actions([col])
        mock_confirm_delete.return_value = True
        req_item = harness.model.item(0).child(0)
        with patch_delete_context_menu(harness.view, req_item.index(), action_count=3):
            harness.actions.show_context_menu(QPoint(0, 0))
        harness.metrics.track_gui_collection_delete_action.assert_has_calls(
            [call("request", "selected"), call("request", "succeeded")]
        )
        self.assertEqual(harness.model.item(0).rowCount(), 0)

    @patch(
        "pypost.ui.presenters.collection_tree_actions.CollectionTreeActions.handle_delete"
    )
    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_delete_no_skips_handle_delete(self, mock_confirm_delete, mock_handle_delete):
        col = make_collection("c1", "My API")
        harness = build_isolated_tree_actions([col])
        mock_confirm_delete.return_value = False
        item = harness.model.item(0)
        with patch_delete_context_menu(harness.view, item.index(), action_count=2):
            harness.actions.show_context_menu(QPoint(0, 0))
        mock_handle_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
