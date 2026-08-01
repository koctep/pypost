"""User-visible strings for the collection import UI (PYPOST-987)."""
from __future__ import annotations

DIALOG_TITLE_IMPORT_COLLECTION = "Import Collection"
DIALOG_TITLE_IMPORT_COLLECTION_CONFLICT = "Import Conflict"

BUTTON_IMPORT_COLLECTION = "Import Collection…"

IMPORT_COLLECTION_FILE_DIALOG_CAPTION = "Import Collection"
IMPORT_COLLECTION_FILE_DIALOG_FILTER = "JSON Files (*.json);;All Files (*)"

MSG_IMPORT_COLLECTION_CONFLICT = (
    'A collection named "{name}" already exists. What do you want to do with '
    "the imported version?"
)
MSG_IMPORT_NO_VALID_COLLECTIONS = "No valid collections found in this file."

MSG_FILE_UNREADABLE = "Could not read file: {reason}"
MSG_FILE_NOT_JSON = "File is not valid JSON: {reason}"
MSG_FILE_WRONG_ROOT = "File must contain a JSON object or a list of collection objects."
MSG_FILE_ENTRY_NOT_OBJECT = "Each collection entry in the file must be a JSON object."

MSG_ENTRY_MISSING_NAME = 'missing or empty "name" field'
MSG_ENTRY_REQUESTS_NOT_LIST = 'the "requests" field must be a list'

LABEL_UNNAMED_ENTRY = "Entry {index}"

SUMMARY_COLLECTIONS_ADDED = "Collections added: {count}"
SUMMARY_COLLECTIONS_UPDATED = "Collections updated: {count}"
SUMMARY_COLLECTIONS_SKIPPED = "Collections skipped: {count}"
SUMMARY_COLLECTIONS_RENAMED = "Collections renamed: {count}"
SUMMARY_REQUESTS_IMPORTED = "Requests imported: {count}"
SUMMARY_RENAMED_HEADER = "Renamed on import:"
SUMMARY_ERRORS_HEADER = "Entries that failed to import:"


def format_collection_import_conflict_message(name: str) -> str:
    return MSG_IMPORT_COLLECTION_CONFLICT.format(name=name)


def format_collection_entry_error(label: str, reason: str) -> str:
    return f"{label}: {reason}"


def format_unnamed_entry_label(index: int) -> str:
    return LABEL_UNNAMED_ENTRY.format(index=index)
