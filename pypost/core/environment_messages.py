"""User-visible strings for environment management UI and validation."""

DIALOG_TITLE_MANAGE_ENVIRONMENTS = "Manage Environments"
DIALOG_TITLE_NEW_ENVIRONMENT = "New Environment"
DIALOG_TITLE_COPY_ENVIRONMENT = "Copy Environment"
DIALOG_TITLE_DELETE_ENVIRONMENT = "Delete Environment"

INPUT_LABEL_NAME = "Name:"

BUTTON_ADD = "Add"

ACTION_RENAME = "Rename"
ACTION_COPY = "Copy"
ACTION_DELETE = "Delete"
ACTION_MOVE_UP = "Move Up"
ACTION_MOVE_DOWN = "Move Down"

COLUMN_VARIABLE = "Variable"
COLUMN_VALUE = "Value"
COLUMN_HIDDEN = "Hidden"

MCP_ENABLE_LABEL = "Enable MCP (Model Context Protocol)"

MSG_EMPTY_NAME = "Name cannot be empty."
MSG_DELETE_ENVIRONMENT_CONFIRM = 'Are you sure you want to delete "{name}"?'
MSG_DUPLICATE_ENVIRONMENT_NAME = 'An environment named "{name}" already exists.'
MSG_COPY_OF_NAME = "Copy of {name}"


def format_delete_environment_confirm(name: str) -> str:
    return MSG_DELETE_ENVIRONMENT_CONFIRM.format(name=name)


def format_duplicate_environment_name(name: str) -> str:
    return MSG_DUPLICATE_ENVIRONMENT_NAME.format(name=name)


def format_copy_of_name(name: str) -> str:
    return MSG_COPY_OF_NAME.format(name=name)
