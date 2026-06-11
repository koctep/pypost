"""Shared QMessageBox helpers for collection item rename and delete flows."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

_RENAME_TITLE = "Rename Error"
_DELETE_TITLE = "Delete Error"


def confirm_delete(parent: QWidget, item_label: str) -> bool:
    """Ask the user to confirm deleting a collection tree item."""
    reply = QMessageBox.question(
        parent,
        "Confirm Delete",
        f"Delete '{item_label}'?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes


def show_rename_empty_name_error(parent: QWidget) -> None:
    QMessageBox.warning(parent, _RENAME_TITLE, "Name cannot be empty.")


def show_rename_failure(parent: QWidget, item_label: str, error: BaseException) -> None:
    QMessageBox.critical(parent, _RENAME_TITLE, f"Failed to rename '{item_label}': {error}")


def show_rename_not_found(parent: QWidget, item_label: str) -> None:
    QMessageBox.warning(parent, _RENAME_TITLE, f"Could not rename '{item_label}'.")


def show_delete_failure(parent: QWidget, item_label: str, error: BaseException) -> None:
    QMessageBox.critical(parent, _DELETE_TITLE, f"Failed to delete '{item_label}': {error}")


def show_delete_not_found(parent: QWidget, item_label: str) -> None:
    QMessageBox.warning(parent, _DELETE_TITLE, f"Could not delete '{item_label}'.")
