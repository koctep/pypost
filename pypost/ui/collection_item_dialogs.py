"""Shared QMessageBox helpers for collection, tab, environment, and history flows."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from pypost.core.environment_messages import (
    DIALOG_TITLE_COPY_ENVIRONMENT,
    DIALOG_TITLE_DELETE_ENVIRONMENT,
    MSG_EMPTY_NAME,
    format_delete_environment_confirm,
    format_duplicate_environment_name,
)

_RENAME_TITLE = "Rename Error"
_DELETE_TITLE = "Delete Error"
_SAVED_REQUEST_CHANGED_TITLE = "Saved Request Changed"


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
    QMessageBox.warning(parent, _RENAME_TITLE, MSG_EMPTY_NAME)


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
        DIALOG_TITLE_DELETE_ENVIRONMENT,
        format_delete_environment_confirm(env_name),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def show_copy_environment_empty_name_error(parent: QWidget) -> None:
    QMessageBox.warning(parent, DIALOG_TITLE_COPY_ENVIRONMENT, MSG_EMPTY_NAME)


def show_copy_environment_duplicate_name_error(parent: QWidget, name: str) -> None:
    QMessageBox.warning(
        parent,
        DIALOG_TITLE_COPY_ENVIRONMENT,
        format_duplicate_environment_name(name),
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


def show_env_save_failed(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, "Save Failed", message)


def show_no_environment_selected(parent: QWidget) -> None:
    QMessageBox.warning(
        parent,
        "No Environment",
        "Please select an environment to set variables.",
    )


def show_invalid_variable_name_error(parent: QWidget, error_msg: str) -> None:
    QMessageBox.warning(parent, "Invalid Variable Name", error_msg)


def show_mcp_server_start_failed(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, "MCP Server Failed to Start", message)


def show_metrics_server_start_failed(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, "Metrics Server Failed to Start", message)


def show_save_request_name_required(parent: QWidget) -> None:
    QMessageBox.warning(parent, "Error", "Please enter a request name")


def show_save_collection_name_required(parent: QWidget) -> None:
    QMessageBox.warning(parent, "Error", "Please enter a new collection name")


def confirm_overwrite_request(parent: QWidget, message: str) -> bool:
    reply = QMessageBox.question(
        parent,
        "Overwrite Request?",
        message,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes


def confirm_overwrite_newer_saved_version(parent: QWidget) -> bool:
    reply = QMessageBox.question(
        parent,
        "Overwrite Newer Saved Version?",
        (
            "A newer version of this request was saved in another tab. "
            "Saving now will replace it on disk. Continue?"
        ),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes


def show_migration_result(parent: QWidget, title: str, body: str, *, success: bool) -> None:
    if success:
        QMessageBox.information(parent, title, body)
    else:
        QMessageBox.warning(parent, title, body)


def confirm_re_encrypt_environments(parent: QWidget) -> bool:
    reply = QMessageBox.question(
        parent,
        "Re-encrypt all environments",
        "This rewrites all encrypted hidden values under the current active key. "
        "A timestamped backup of environments.json is created before writing.\n\n"
        "Continue?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def show_invalid_retryable_status_codes(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, "Invalid retryable status codes", message)
