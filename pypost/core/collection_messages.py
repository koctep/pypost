"""User-visible strings for the collection import and export UI."""

from __future__ import annotations

DIALOG_TITLE_IMPORT_COLLECTION = "Import Collection"
DIALOG_TITLE_IMPORT_COLLECTION_CONFLICT = "Import Conflict"
DIALOG_TITLE_EXPORT_COLLECTION = "Export Collection"
DIALOG_TITLE_EXPORT_ALL_COLLECTIONS = "Export All Collections"

BUTTON_IMPORT_COLLECTION = "Import Collection…"
BUTTON_IMPORT_COLLECTION_FROM_FILE = "From File"
BUTTON_IMPORT_COLLECTION_FROM_LIBRARY = "From Library"
BUTTON_EXPORT_COLLECTION = "Export Collection…"
BUTTON_EXPORT_ALL_COLLECTIONS = "Export All Collections…"

EXPORT_COLLECTION_FILE_DIALOG_CAPTION = "Export Collection"
EXPORT_COLLECTION_FILE_DIALOG_FILTER = "JSON Files (*.json);;All Files (*)"
EXPORT_ALL_COLLECTIONS_FILE_DIALOG_CAPTION = "Export All Collections"
EXPORT_ALL_COLLECTIONS_SUGGESTED_FILENAME = "collections.json"

MSG_EXPORT_NO_COLLECTION_SELECTED = (
    "Select a collection in the tree to export it (click the collection name, "
    "not only a request)."
)

IMPORT_COLLECTION_FILE_DIALOG_CAPTION = "Import Collection"
IMPORT_COLLECTION_FILE_DIALOG_FILTER = "JSON Files (*.json);;All Files (*)"
DIALOG_TITLE_IMPORT_COLLECTION_LIBRARY = "Import Collections from Library"
DIALOG_TITLE_IMPORT_COLLECTION_LIBRARY_MODE = "Library Import Mode"

MSG_IMPORT_COLLECTION_CONFLICT = (
    'A collection named "{name}" already exists. What do you want to do with '
    "the imported version?"
)
MSG_IMPORT_NO_VALID_COLLECTIONS = "No valid collections found in this file."
MSG_IMPORT_PREPARING = "Preparing collection import…"
MSG_IMPORT_VALIDATING = "Validating collections ({done}/{total})…"
MSG_IMPORT_LIBRARY_NO_COLLECTIONS = (
    "No importable collections were found in the connected libraries."
)
MSG_IMPORT_LIBRARY_UNAVAILABLE = (
    "Connected library collections are unavailable. Check the library connection and retry."
)
MSG_IMPORT_LIBRARY_MODE = "How should the selected library collections be imported?"

MSG_FILE_UNREADABLE = "Could not read file: {reason}"
MSG_FILE_NOT_JSON = "File is not valid JSON: {reason}"
MSG_FILE_WRONG_ROOT = "File must contain a JSON object or a list of collection objects."
MSG_FILE_ENTRY_NOT_OBJECT = "Each collection entry in the file must be a JSON object."

MSG_ENTRY_MISSING_NAME = 'missing or empty "name" field'
MSG_ENTRY_REQUESTS_NOT_LIST = 'the "requests" field must be a list'
MSG_ENTRY_WEBSOCKETS_NOT_LIST = 'the "websockets" field must be a list'
MSG_ENTRY_MCP_CLIENTS_NOT_LIST = 'the "mcp_clients" field must be a list'

LABEL_UNNAMED_ENTRY = "Entry {index}"

SUMMARY_COLLECTIONS_ADDED = "Collections added: {count}"
SUMMARY_COLLECTIONS_UPDATED = "Collections updated: {count}"
SUMMARY_COLLECTIONS_SKIPPED = "Collections skipped: {count}"
SUMMARY_COLLECTIONS_RENAMED = "Collections renamed: {count}"
SUMMARY_REQUESTS_IMPORTED = "Requests imported: {count}"
SUMMARY_WEBSOCKETS_IMPORTED = "WebSockets imported: {count}"
SUMMARY_RENAMED_HEADER = "Renamed on import:"
SUMMARY_ERRORS_HEADER = "Entries that failed to import:"
BUTTON_IMPORT_LIBRARY_COPY = "Copy"
BUTTON_IMPORT_LIBRARY_LINK = "Link"


def format_collection_import_conflict_message(name: str) -> str:
    return MSG_IMPORT_COLLECTION_CONFLICT.format(name=name)


def format_collection_entry_error(label: str, reason: str) -> str:
    return f"{label}: {reason}"


def format_unnamed_entry_label(index: int) -> str:
    return LABEL_UNNAMED_ENTRY.format(index=index)


def format_import_validating_message(done: int, total: int) -> str:
    return MSG_IMPORT_VALIDATING.format(done=done, total=total)


def format_collection_import_progress(done: int, total: int) -> str:
    return format_import_validating_message(done, total)
