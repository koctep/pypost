"""Pure logic for exporting a collection to a file (PYPOST-989).

No Qt dependency: payload shaping and file writing are directly unit-testable
without a QApplication. Qt-facing dialogs live in
``pypost.ui.collection_item_dialogs``; orchestration lives in
``CollectionExportActions``.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from pypost.core.export_file_writer import write_json_export_file
from pypost.models.models import Collection

logger = logging.getLogger(__name__)

__all__ = [
    "CollectionExportError",
    "CollectionExportResult",
    "CollectionsExportResult",
    "build_all_export_payload",
    "build_export_payload",
    "collection_for_export",
    "format_all_export_result",
    "format_export_result",
    "suggested_export_filename",
    "write_export_file",
]


class CollectionExportError(Exception):
    """Raised when an export file cannot be written."""


@dataclass(frozen=True)
class CollectionExportResult:
    """Summary of a completed collection export."""

    collection_name: str
    request_count: int
    path: Path
    websocket_count: int = 0


@dataclass(frozen=True)
class CollectionsExportResult:
    """Summary of a completed all-collections export."""

    collection_count: int
    request_count: int
    path: Path
    websocket_count: int = 0


def collection_for_export(
    collections: list[Collection],
    *,
    selected_collection_id: str | None,
) -> Collection | None:
    """Return the collection to export for the selected tree id, or None."""
    if not selected_collection_id:
        return None
    for collection in collections:
        if collection.id == selected_collection_id:
            return collection
    return None


def suggested_export_filename(collection: Collection) -> str:
    """Default save-dialog filename for one collection."""
    safe_name = collection.name.strip() or "collection"
    for char in '\\/:*?"<>|':
        safe_name = safe_name.replace(char, "_")
    return f"{safe_name}.json"


def build_export_payload(collection: Collection) -> dict:
    """Serialize one collection into native PyPost JSON import shape."""
    payload = collection.model_dump(mode="json")
    logger.info(
        "collection_export_payload_built collection_name=%s request_count=%d websocket_count=%d",
        collection.name,
        len(collection.requests),
        len(getattr(collection, "websockets", [])),
    )
    return payload


def build_all_export_payload(collections: list[Collection]) -> list[dict]:
    """Serialize collections in order into the native JSON-list import shape."""
    payload = [build_export_payload(collection) for collection in collections]
    total_requests = sum(len(c.requests) for c in collections)
    total_websockets = sum(len(getattr(c, "websockets", [])) for c in collections)
    logger.info(
        "collections_export_payload_built collection_count=%d request_count=%d websocket_count=%d",
        len(payload),
        total_requests,
        total_websockets,
    )
    return payload


def write_export_file(path: Path, payload: dict | list[dict]) -> None:
    """Write the export payload to ``path`` as indented UTF-8 JSON."""
    write_json_export_file(path, payload, error_cls=CollectionExportError)
    logger.info("collection_export_file_written path=%s", path)


def format_export_result(result: CollectionExportResult) -> str:
    """Human-readable summary for the export result dialog."""
    if result.websocket_count > 0:
        counts = f"{result.request_count} request(s), {result.websocket_count} websocket(s)"
    else:
        counts = f"{result.request_count} request(s)"
    lines = [
        f'Exported collection "{result.collection_name}" ({counts}) to:',
        str(result.path),
    ]
    return "\n".join(lines)


def format_all_export_result(result: CollectionsExportResult) -> str:
    """Human-readable summary for the all-collections export result dialog."""
    if result.websocket_count > 0:
        counts = f"{result.request_count} request(s), {result.websocket_count} websocket(s)"
    else:
        counts = f"{result.request_count} request(s)"
    lines = [
        f"Exported {result.collection_count} collection(s) ({counts}) to:",
        str(result.path),
    ]
    return "\n".join(lines)
