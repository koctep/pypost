"""User-visible strings for environment management UI and validation."""
from __future__ import annotations

DIALOG_TITLE_MANAGE_ENVIRONMENTS = "Manage Environments"
DIALOG_TITLE_NEW_ENVIRONMENT = "New Environment"
DIALOG_TITLE_COPY_ENVIRONMENT = "Copy Environment"
DIALOG_TITLE_DELETE_ENVIRONMENT = "Delete Environment"
DIALOG_TITLE_IMPORT_ENVIRONMENTS = "Import Environments"
DIALOG_TITLE_IMPORT_CONFLICT = "Import Conflict"

INPUT_LABEL_NAME = "Name:"

BUTTON_ADD = "Add"
BUTTON_IMPORT = "Import…"

IMPORT_FILE_DIALOG_CAPTION = "Import Environments"
IMPORT_FILE_DIALOG_FILTER = "JSON Files (*.json);;All Files (*)"

BUTTON_OVERWRITE = "Overwrite"
BUTTON_KEEP_BOTH = "Keep Both"
BUTTON_SKIP = "Skip"
CHECKBOX_APPLY_TO_ALL_CONFLICTS = "Apply to all remaining conflicts"

ACTION_RENAME = "Rename"
ACTION_COPY = "Copy"
ACTION_DELETE = "Delete"
ACTION_MOVE_UP = "Move Up"
ACTION_MOVE_DOWN = "Move Down"

COLUMN_VARIABLE = "Variable"
COLUMN_VALUE = "Value"
COLUMN_HIDDEN = "Hidden"

MCP_ENABLE_LABEL = "Enable MCP (Model Context Protocol)"
MCP_ENABLE_TOOLTIP = (
    "When enabled, every request marked Expose as MCP in any loaded collection "
    "is registered as a tool for this environment. There is no per-collection gate."
)

MSG_EMPTY_NAME = "Name cannot be empty."
MSG_DELETE_ENVIRONMENT_CONFIRM = 'Are you sure you want to delete "{name}"?'
MSG_DUPLICATE_ENVIRONMENT_NAME = 'An environment named "{name}" already exists.'
MSG_COPY_OF_NAME = "Copy of {name}"
MSG_IMPORT_CONFLICT = (
    'An environment named "{name}" already exists. What do you want to do with '
    "the imported version?"
)
MSG_IMPORT_NO_VALID_ENVIRONMENTS = "No valid environments found in this file."


def format_delete_environment_confirm(name: str) -> str:
    return MSG_DELETE_ENVIRONMENT_CONFIRM.format(name=name)


def format_duplicate_environment_name(name: str) -> str:
    return MSG_DUPLICATE_ENVIRONMENT_NAME.format(name=name)


def format_copy_of_name(name: str) -> str:
    return MSG_COPY_OF_NAME.format(name=name)


def format_import_conflict_message(name: str) -> str:
    return MSG_IMPORT_CONFLICT.format(name=name)
