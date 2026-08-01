"""Shared QMessageBox helpers for collection, tab, environment, and history flows."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QCheckBox, QFileDialog, QMessageBox, QWidget

from pypost.core.collection_messages import (
    DIALOG_TITLE_IMPORT_COLLECTION,
    DIALOG_TITLE_IMPORT_COLLECTION_CONFLICT,
    IMPORT_COLLECTION_FILE_DIALOG_CAPTION,
    IMPORT_COLLECTION_FILE_DIALOG_FILTER,
    format_collection_import_conflict_message,
)
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.core.environment_export import ExportScope
from pypost.core.environment_messages import (
    BUTTON_EXPORT_ALL,
    BUTTON_EXPORT_SELECTED,
    BUTTON_KEEP_BOTH,
    BUTTON_OVERWRITE,
    BUTTON_SKIP,
    CHECKBOX_APPLY_TO_ALL_CONFLICTS,
    DIALOG_TITLE_COPY_ENVIRONMENT,
    DIALOG_TITLE_DELETE_ENVIRONMENT,
    DIALOG_TITLE_EXPORT_ENVIRONMENTS,
    DIALOG_TITLE_EXPORT_SCOPE,
    DIALOG_TITLE_EXPORT_SECRETS,
    DIALOG_TITLE_IMPORT_CONFLICT,
    DIALOG_TITLE_IMPORT_ENVIRONMENTS,
    EXPORT_FILE_DIALOG_CAPTION,
    EXPORT_FILE_DIALOG_FILTER,
    IMPORT_FILE_DIALOG_CAPTION,
    IMPORT_FILE_DIALOG_FILTER,
    MSG_EMPTY_NAME,
    MSG_EXPORT_NO_SELECTION,
    format_delete_environment_confirm,
    format_duplicate_environment_name,
    format_export_secrets_warning,
    format_import_conflict_message,
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


def confirm_encrypt_plaintext_hidden(parent: QWidget) -> bool:
    reply = QMessageBox.question(
        parent,
        "Encrypt plaintext hidden values",
        "This encrypts hidden environment variables that are still stored as "
        "plaintext strings. A timestamped backup of environments.json is created "
        "before writing.\n\nContinue?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def prompt_import_environments_file(parent: QWidget) -> Path | None:
    """Open a file picker for an environment import file; None on Cancel."""
    path_str, _selected_filter = QFileDialog.getOpenFileName(
        parent,
        IMPORT_FILE_DIALOG_CAPTION,
        "",
        IMPORT_FILE_DIALOG_FILTER,
    )
    if not path_str:
        return None
    return Path(path_str)


def show_import_invalid_file_error(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, DIALOG_TITLE_IMPORT_ENVIRONMENTS, message)


def _prompt_import_conflict_box(
    parent: QWidget, title: str, message: str, *, remaining_count: int
) -> tuple[ImportConflictDecision, bool]:
    """Overwrite / Keep Both / Skip box shared by every import flow.

    Returns the chosen decision and whether it should apply to all remaining
    conflicts in this import (via the "apply to all" checkbox).
    """
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(message)
    overwrite_btn = box.addButton(BUTTON_OVERWRITE, QMessageBox.ButtonRole.DestructiveRole)
    keep_both_btn = box.addButton(BUTTON_KEEP_BOTH, QMessageBox.ButtonRole.AcceptRole)
    box.addButton(BUTTON_SKIP, QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(keep_both_btn)

    apply_to_all_checkbox: QCheckBox | None = None
    if remaining_count > 0:
        apply_to_all_checkbox = QCheckBox(CHECKBOX_APPLY_TO_ALL_CONFLICTS)
        box.setCheckBox(apply_to_all_checkbox)

    box.exec()
    clicked = box.clickedButton()
    if clicked is overwrite_btn:
        decision = ImportConflictDecision.OVERWRITE
    elif clicked is keep_both_btn:
        decision = ImportConflictDecision.KEEP_BOTH
    else:
        decision = ImportConflictDecision.SKIP

    apply_to_all = apply_to_all_checkbox is not None and apply_to_all_checkbox.isChecked()
    return decision, apply_to_all


def prompt_import_conflict(
    parent: QWidget, name: str, *, remaining_count: int
) -> tuple[ImportConflictDecision, bool]:
    """Ask how to resolve a single environment name conflict during import."""
    return _prompt_import_conflict_box(
        parent,
        DIALOG_TITLE_IMPORT_CONFLICT,
        format_import_conflict_message(name),
        remaining_count=remaining_count,
    )


def show_import_result(parent: QWidget, summary_text: str, *, success: bool) -> None:
    if success:
        QMessageBox.information(parent, DIALOG_TITLE_IMPORT_ENVIRONMENTS, summary_text)
    else:
        QMessageBox.warning(parent, DIALOG_TITLE_IMPORT_ENVIRONMENTS, summary_text)


def prompt_export_scope(parent: QWidget) -> ExportScope | None:
    """Ask whether to export the selected environment or all environments."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(DIALOG_TITLE_EXPORT_SCOPE)
    box.setText("Which environments do you want to export?")
    selected_btn = box.addButton(
        BUTTON_EXPORT_SELECTED, QMessageBox.ButtonRole.AcceptRole
    )
    all_btn = box.addButton(BUTTON_EXPORT_ALL, QMessageBox.ButtonRole.AcceptRole)
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.setDefaultButton(all_btn)
    box.exec()
    clicked = box.clickedButton()
    if clicked is selected_btn:
        return ExportScope.SELECTED
    if clicked is all_btn:
        return ExportScope.ALL
    return None


def show_export_no_selection_error(parent: QWidget) -> None:
    QMessageBox.warning(parent, DIALOG_TITLE_EXPORT_ENVIRONMENTS, MSG_EXPORT_NO_SELECTION)


def confirm_export_includes_secrets(parent: QWidget, environment_names: list[str]) -> bool:
    reply = QMessageBox.warning(
        parent,
        DIALOG_TITLE_EXPORT_SECRETS,
        format_export_secrets_warning(environment_names),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def prompt_export_environments_file(parent: QWidget, *, suggested_name: str) -> Path | None:
    """Open a save dialog for an environment export file; None on Cancel."""
    path_str, _selected_filter = QFileDialog.getSaveFileName(
        parent,
        EXPORT_FILE_DIALOG_CAPTION,
        suggested_name,
        EXPORT_FILE_DIALOG_FILTER,
    )
    if not path_str:
        return None
    return Path(path_str)


def show_export_result(parent: QWidget, summary_text: str, *, success: bool) -> None:
    if success:
        QMessageBox.information(parent, DIALOG_TITLE_EXPORT_ENVIRONMENTS, summary_text)
    else:
        QMessageBox.warning(parent, DIALOG_TITLE_EXPORT_ENVIRONMENTS, summary_text)


def show_export_error(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, DIALOG_TITLE_EXPORT_ENVIRONMENTS, message)


def prompt_import_collection_file(parent: QWidget) -> Path | None:
    """Open a file picker for a collection import file; None on Cancel."""
    path_str, _selected_filter = QFileDialog.getOpenFileName(
        parent,
        IMPORT_COLLECTION_FILE_DIALOG_CAPTION,
        "",
        IMPORT_COLLECTION_FILE_DIALOG_FILTER,
    )
    if not path_str:
        return None
    return Path(path_str)


def show_collection_import_invalid_file_error(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, DIALOG_TITLE_IMPORT_COLLECTION, message)


def prompt_collection_import_conflict(
    parent: QWidget, name: str, *, remaining_count: int
) -> tuple[ImportConflictDecision, bool]:
    """Ask how to resolve a single collection name conflict during import."""
    return _prompt_import_conflict_box(
        parent,
        DIALOG_TITLE_IMPORT_COLLECTION_CONFLICT,
        format_collection_import_conflict_message(name),
        remaining_count=remaining_count,
    )


def show_collection_import_result(
    parent: QWidget, summary_text: str, *, success: bool
) -> None:
    if success:
        QMessageBox.information(parent, DIALOG_TITLE_IMPORT_COLLECTION, summary_text)
    else:
        QMessageBox.warning(parent, DIALOG_TITLE_IMPORT_COLLECTION, summary_text)


def show_invalid_retryable_status_codes(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, "Invalid retryable status codes", message)


def show_invalid_bind_address(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, "Invalid server address", message)
