"""Unit tests for collection item QMessageBox helpers."""

import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from pypost.ui.collection_item_dialogs import (
    confirm_delete,
    show_delete_failure,
    show_delete_not_found,
    show_rename_empty_name_error,
    show_rename_failure,
    show_rename_not_found,
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


if __name__ == "__main__":
    unittest.main()
