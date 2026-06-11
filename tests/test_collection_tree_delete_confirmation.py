"""Direct unit tests for delete confirmation branching in CollectionTreeActions."""

import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, call, patch

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

from tests.collection_tree_actions_test_support import (
    build_isolated_tree_actions,
    make_collection,
    make_request,
)


class TestCollectionTreeDeleteConfirmation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @contextmanager
    def _delete_via_menu(self, harness, item_index, *, action_count):
        rename_action = MagicMock()
        delete_action = MagicMock()
        if action_count == 2:
            side_effect = [rename_action, delete_action]
        else:
            new_tab_action = MagicMock()
            side_effect = [new_tab_action, rename_action, delete_action]
        with patch.object(harness.view, "indexAt", return_value=item_index):
            with patch("pypost.ui.presenters.collection_tree_actions.QMenu") as mock_menu_class:
                mock_menu = MagicMock()
                mock_menu.addAction.side_effect = side_effect
                mock_menu.exec.return_value = delete_action
                mock_menu_class.return_value = mock_menu
                yield delete_action

    @patch("pypost.ui.presenters.collection_tree_actions.confirm_delete")
    def test_collection_delete_no_records_cancelled_metric(self, mock_confirm_delete):
        col = make_collection("c1", "My API")
        harness = build_isolated_tree_actions([col])
        mock_confirm_delete.return_value = False
        item = harness.model.item(0)
        with self._delete_via_menu(harness, item.index(), action_count=2):
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
        with self._delete_via_menu(harness, item.index(), action_count=2):
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
        with self._delete_via_menu(harness, req_item.index(), action_count=3):
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
        with self._delete_via_menu(harness, req_item.index(), action_count=3):
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
        with self._delete_via_menu(harness, item.index(), action_count=2):
            harness.actions.show_context_menu(QPoint(0, 0))
        mock_handle_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
