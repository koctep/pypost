"""Shared QMessageBox helpers for collection, tab, environment, and history flows."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

_RENAME_TITLE = "Rename Error"
_DELETE_TITLE = "Delete Error"
_SAVED_REQUEST_CHANGED_TITLE = "Saved Request Changed"
_COPY_ENVIRONMENT_TITLE = "Copy Environment"


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


def show_request_failed_error(parent: QWidget, error: str) -> None:
    QMessageBox.critical(parent, "Error", f"Request failed: {error}")


def show_request_error(parent: QWidget, message: str) -> None:
    QMessageBox.critical(parent, "Request Error", message)


def prompt_dirty_sibling_tab_reload(parent: QWidget, name: str) -> bool:
    """Ask whether to load the latest persisted copy when a dirty sibling tab saved."""
    message = (
        f"'{name}' was saved in another tab. Your unsaved changes may be "
        "outdated relative to what is on disk."
    )
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(_SAVED_REQUEST_CHANGED_TITLE)
    box.setText(message)
    keep_btn = box.addButton("Keep my changes", QMessageBox.RejectRole)
    load_btn = box.addButton("Load latest", QMessageBox.AcceptRole)
    box.setDefaultButton(keep_btn)
    box.exec()
    return box.clickedButton() is load_btn


def prompt_clean_sibling_tab_reload(parent: QWidget, name: str) -> bool:
    """Ask whether to load the latest persisted copy when a clean sibling tab saved."""
    message = (
        f"'{name}' was saved in another tab. This tab may show outdated "
        "saved content."
    )
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(_SAVED_REQUEST_CHANGED_TITLE)
    box.setText(message)
    dismiss_btn = box.addButton("Dismiss", QMessageBox.RejectRole)
    load_btn = box.addButton("Load latest", QMessageBox.AcceptRole)
    box.setDefaultButton(dismiss_btn)
    box.exec()
    return box.clickedButton() is load_btn


def confirm_delete_environment(parent: QWidget, env_name: str) -> bool:
    reply = QMessageBox.question(
        parent,
        "Delete Environment",
        f'Are you sure you want to delete "{env_name}"?',
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def show_copy_environment_empty_name_error(parent: QWidget) -> None:
    QMessageBox.warning(parent, _COPY_ENVIRONMENT_TITLE, "Name cannot be empty.")


def show_copy_environment_duplicate_name_error(parent: QWidget, name: str) -> None:
    QMessageBox.warning(
        parent,
        _COPY_ENVIRONMENT_TITLE,
        f'An environment named "{name}" already exists.',
    )


def confirm_clear_history(parent: QWidget) -> bool:
    reply = QMessageBox.question(
        parent,
        "Clear History",
        "Are you sure you want to clear all request history?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes
