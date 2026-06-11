"""Unit tests for collection item QMessageBox helpers."""

import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from pypost.ui.collection_item_dialogs import (
    confirm_clear_history,
    confirm_delete,
    confirm_delete_environment,
    prompt_clean_sibling_tab_reload,
    prompt_dirty_sibling_tab_reload,
    show_copy_environment_duplicate_name_error,
    show_copy_environment_empty_name_error,
    show_delete_failure,
    show_delete_not_found,
    show_rename_empty_name_error,
    show_rename_failure,
    show_rename_not_found,
    show_request_error,
    show_request_failed_error,
)


class TestCollectionItemDialogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.parent = QWidget()

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.question")
    def test_confirm_delete_returns_true_on_yes(self, mock_question):
        mock_question.return_value = QMessageBox.Yes
        self.assertTrue(confirm_delete(self.parent, "My API"))
        mock_question.assert_called_once()
        self.assertIn("My API", mock_question.call_args.args[2])

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.question")
    def test_confirm_delete_returns_false_on_no(self, mock_question):
        mock_question.return_value = QMessageBox.No
        self.assertFalse(confirm_delete(self.parent, "My API"))

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.warning")
    def test_show_rename_empty_name_error(self, mock_warning):
        show_rename_empty_name_error(self.parent)
        mock_warning.assert_called_once_with(self.parent, "Rename Error", "Name cannot be empty.")

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.critical")
    def test_show_rename_failure(self, mock_critical):
        show_rename_failure(self.parent, "Old Name", RuntimeError("disk full"))
        mock_critical.assert_called_once_with(
            self.parent,
            "Rename Error",
            "Failed to rename 'Old Name': disk full",
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.warning")
    def test_show_rename_not_found(self, mock_warning):
        show_rename_not_found(self.parent, "Old Name")
        mock_warning.assert_called_once_with(
            self.parent,
            "Rename Error",
            "Could not rename 'Old Name'.",
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.critical")
    def test_show_delete_failure(self, mock_critical):
        show_delete_failure(self.parent, "My API", OSError("permission denied"))
        mock_critical.assert_called_once_with(
            self.parent,
            "Delete Error",
            "Failed to delete 'My API': permission denied",
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.warning")
    def test_show_delete_not_found(self, mock_warning):
        show_delete_not_found(self.parent, "My API")
        mock_warning.assert_called_once_with(
            self.parent,
            "Delete Error",
            "Could not delete 'My API'.",
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.critical")
    def test_show_request_failed_error(self, mock_critical):
        show_request_failed_error(self.parent, "connection refused")
        mock_critical.assert_called_once_with(
            self.parent,
            "Error",
            "Request failed: connection refused",
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.critical")
    def test_show_request_error(self, mock_critical):
        show_request_error(self.parent, "Timed out waiting for response.")
        mock_critical.assert_called_once_with(
            self.parent,
            "Request Error",
            "Timed out waiting for response.",
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox")
    def test_prompt_dirty_sibling_tab_reload_load_latest(self, mock_mb):
        mock_box = mock_mb.return_value
        keep_btn = object()
        load_btn = object()
        mock_box.addButton.side_effect = [keep_btn, load_btn]
        mock_box.clickedButton.return_value = load_btn
        self.assertTrue(prompt_dirty_sibling_tab_reload(self.parent, "Shared"))
        mock_box.exec.assert_called_once()

    @patch("pypost.ui.collection_item_dialogs.QMessageBox")
    def test_prompt_clean_sibling_tab_reload_dismiss(self, mock_mb):
        mock_box = mock_mb.return_value
        dismiss_btn = object()
        load_btn = object()
        mock_box.addButton.side_effect = [dismiss_btn, load_btn]
        mock_box.clickedButton.return_value = dismiss_btn
        self.assertFalse(prompt_clean_sibling_tab_reload(self.parent, "Shared"))

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.question")
    def test_confirm_delete_environment_returns_true_on_yes(self, mock_question):
        mock_question.return_value = QMessageBox.StandardButton.Yes
        self.assertTrue(confirm_delete_environment(self.parent, "Staging"))

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.warning")
    def test_show_copy_environment_empty_name_error(self, mock_warning):
        show_copy_environment_empty_name_error(self.parent)
        mock_warning.assert_called_once_with(
            self.parent,
            "Copy Environment",
            "Name cannot be empty.",
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.warning")
    def test_show_copy_environment_duplicate_name_error(self, mock_warning):
        show_copy_environment_duplicate_name_error(self.parent, "Staging")
        mock_warning.assert_called_once_with(
            self.parent,
            "Copy Environment",
            'An environment named "Staging" already exists.',
        )

    @patch("pypost.ui.collection_item_dialogs.QMessageBox.question")
    def test_confirm_clear_history_returns_false_on_no(self, mock_question):
        mock_question.return_value = QMessageBox.No
        self.assertFalse(confirm_clear_history(self.parent))


if __name__ == "__main__":
    unittest.main()
