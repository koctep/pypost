"""Pure logic for importing collections from a file (PYPOST-987).

No Qt and no storage dependency: parsing, shape validation, conflict detection,
identifier reservation, and planning are all directly unit-testable without a
QApplication or a data directory. Qt-facing dialogs live in
``pypost.ui.collection_item_dialogs``; orchestration lives in
``CollectionsPresenter.import_collections``.

The planner never touches disk. It returns both the full target collection list
and the subset that must be persisted, so the caller writes exactly the
collections a decision actually changed.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import uuid

from pydantic import ValidationError

from pypost.core.collection_messages import (
    MSG_ENTRY_MCP_CLIENTS_NOT_LIST,
    MSG_ENTRY_MISSING_NAME,
    MSG_ENTRY_REQUESTS_NOT_LIST,
    MSG_ENTRY_WEBSOCKETS_NOT_LIST,
    MSG_FILE_ENTRY_NOT_OBJECT,
    MSG_FILE_NOT_JSON,
    MSG_FILE_UNREADABLE,
    MSG_FILE_WRONG_ROOT,
    SUMMARY_COLLECTIONS_ADDED,
    SUMMARY_COLLECTIONS_RENAMED,
    SUMMARY_COLLECTIONS_SKIPPED,
    SUMMARY_COLLECTIONS_UPDATED,
    SUMMARY_ERRORS_HEADER,
    SUMMARY_RENAMED_HEADER,
    SUMMARY_REQUESTS_IMPORTED,
    SUMMARY_WEBSOCKETS_IMPORTED,
    format_collection_entry_error,
    format_unnamed_entry_label,
)
from pypost.core.import_conflicts import ImportConflictDecision, generate_import_copy_name
from pypost.models.models import Collection, RequestData
from pypost.models.websocket import WebSocketConnection
import yaml

logger = logging.getLogger(__name__)


class CollectionImportFileError(Exception):
    """Raised for unreadable, malformed, or wrong-shaped import files."""


@dataclass(frozen=True)
class CollectionImportPlanResult:
    """The outcome of planning an import: the new target list plus a summary.

    ``collections`` is the complete list the app should hold afterwards;
    ``persisted`` is the subset whose files must be (re)written. A skipped
    collection appears in neither, so its stored file is left untouched.
    """

    collections: list[Collection]
    persisted: list[Collection]
    added: list[str]
    updated: list[str]
    skipped: list[str]
    renamed: list[tuple[str, str]]
    request_count: int
    parse_errors: list[str]
    websocket_count: int = 0


def _read_records(path: Path) -> list[dict]:
    """Read the file and normalize its JSON or YAML root into a list of records."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("collection_import_file_read_failed path=%s reason=%s", path, exc)
        raise CollectionImportFileError(MSG_FILE_UNREADABLE.format(reason=exc)) from exc

    data: Any = None
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            logger.warning(
                "collection_import_yaml_parse_failed path=%s reason=%s", path, exc
            )
            raise CollectionImportFileError(MSG_FILE_NOT_JSON.format(reason=exc)) from exc
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            try:
                data = yaml.safe_load(text)
                if not isinstance(data, (dict, list)):
                    logger.warning(
                        "collection_import_json_parse_failed path=%s reason=%s", path, exc
                    )
                    raise CollectionImportFileError(MSG_FILE_NOT_JSON.format(reason=exc)) from exc
            except Exception:
                logger.warning(
                    "collection_import_parse_failed path=%s reason=%s", path, exc
                )
                raise CollectionImportFileError(MSG_FILE_NOT_JSON.format(reason=exc)) from exc

    if isinstance(data, dict):
        records = [data]
    elif isinstance(data, list):
        records = data
    else:
        raise CollectionImportFileError(MSG_FILE_WRONG_ROOT)

    if not all(isinstance(item, dict) for item in records):
        raise CollectionImportFileError(MSG_FILE_ENTRY_NOT_OBJECT)
    return records


def _record_label(record: dict, index: int) -> str:
    name = record.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return format_unnamed_entry_label(index)


def _shape_error(record: dict) -> str | None:
    """Reject records Pydantic would happily accept as an empty collection.

    Every ``Collection`` field has a default, so ``Collection(**{"any": 1})``
    validates into a nameless placeholder. Requiring a real ``name`` (and a
    list-shaped ``requests``) is what turns a foreign-tool file into a named
    parse error instead of a phantom empty collection in the tree.
    """
    name = record.get("name")
    if not isinstance(name, str) or not name.strip():
        return MSG_ENTRY_MISSING_NAME
    requests = record.get("requests")
    if requests is not None and not isinstance(requests, list):
        return MSG_ENTRY_REQUESTS_NOT_LIST
    websockets = record.get("websockets")
    if websockets is not None and not isinstance(websockets, list):
        return MSG_ENTRY_WEBSOCKETS_NOT_LIST
    mcp_clients = record.get("mcp_clients")
    if mcp_clients is not None and not isinstance(mcp_clients, list):
        return MSG_ENTRY_MCP_CLIENTS_NOT_LIST
    return None


def load_collection_import_candidates(
    path: Path,
    on_progress: Callable[[int, int], None] | None = None,
) -> tuple[list[Collection], list[str]]:
    """Read and parse an import file into candidate collections.

    Accepts either a JSON list of collection records or a single JSON object
    (normalized to a one-item list), matching what a copy of a stored
    ``collections/<id>.json`` file or a hand-shared bundle looks like.

    Raises:
        CollectionImportFileError: for file-level problems only (unreadable
            file, malformed JSON, a root that is neither a list nor an object,
            or a list element that is not an object). Per-record failures are
            reported through the returned error list instead, so one bad entry
            never blocks the rest of the file.
    """
    records = _read_records(path)
    total_records = len(records)

    collections: list[Collection] = []
    parse_errors: list[str] = []
    for index, record in enumerate(records, start=1):
        label = _record_label(record, index)
        shape_error = _shape_error(record)
        if shape_error is not None:
            parse_errors.append(format_collection_entry_error(label, shape_error))
            if on_progress is not None:
                on_progress(index, total_records)
            continue
        try:
            collections.append(Collection(**record))
        except ValidationError as exc:
            parse_errors.append(format_collection_entry_error(label, str(exc)))
        if on_progress is not None:
            on_progress(index, total_records)

    logger.info(
        "collection_import_file_parsed path=%s candidate_count=%d error_count=%d",
        path,
        len(collections),
        len(parse_errors),
    )
    return collections, parse_errors


def find_collection_conflicts(
    existing: list[Collection], incoming: list[Collection]
) -> list[str]:
    """Names present in both lists, in incoming order, without duplicates."""
    existing_names = {col.name for col in existing}
    conflicts: list[str] = []
    seen: set[str] = set()
    for col in incoming:
        if col.name in existing_names and col.name not in seen:
            conflicts.append(col.name)
            seen.add(col.name)
    return conflicts


def _reserve_requests(
    requests: list[RequestData], taken_request_ids: set[str]
) -> list[RequestData]:
    """Copy requests, minting a fresh id for any that would collide.

    A duplicate request id would shadow an existing request in
    ``RequestManager._request_index`` and silently break open/rename/delete for
    it, so a collision is always resolved rather than carried through.
    """
    reserved: list[RequestData] = []
    for request in requests:
        request_id = request.id
        if request_id in taken_request_ids:
            request_id = str(uuid.uuid4())
        taken_request_ids.add(request_id)
        reserved.append(request.model_copy(update={"id": request_id}, deep=True))
    return reserved


def _reserve_websockets(
    websockets: list[WebSocketConnection], taken_ws_ids: set[str]
) -> list[WebSocketConnection]:
    """Copy websockets, minting a fresh id for any that would collide."""
    reserved: list[WebSocketConnection] = []
    for ws in websockets:
        ws_id = ws.id
        if ws_id in taken_ws_ids:
            ws_id = str(uuid.uuid4())
        taken_ws_ids.add(ws_id)
        reserved.append(ws.model_copy(update={"id": ws_id}, deep=True))
    return reserved


def _materialize(
    source: Collection,
    name: str,
    taken_collection_ids: set[str],
    taken_request_ids: set[str],
    taken_ws_ids: set[str],
) -> Collection:
    """Build the collection to insert, resolving id collisions silently.

    A colliding collection id would make ``StorageManager.save_collection``
    overwrite an unrelated collection's file, so it is replaced; a free id is
    preserved so a clean-machine restore stays faithful.
    """
    collection_id = source.id
    if collection_id in taken_collection_ids:
        collection_id = str(uuid.uuid4())
    taken_collection_ids.add(collection_id)
    library_link = getattr(source, "library_link", None)
    return Collection(
        id=collection_id,
        name=name,
        description=source.description,
        version=source.version,
        variables=[v.model_copy(deep=True) for v in getattr(source, "variables", [])],
        presets=dict(getattr(source, "presets", {})),
        requests=_reserve_requests(source.requests, taken_request_ids),
        websockets=_reserve_websockets(getattr(source, "websockets", []), taken_ws_ids),
        mcp_clients=[mcp.model_copy(deep=True) for mcp in getattr(source, "mcp_clients", [])],
        library_link=(
            library_link.model_copy(deep=True) if library_link is not None else None
        ),
    )


def plan_collection_import(
    existing: list[Collection],
    incoming: list[Collection],
    decisions: dict[str, ImportConflictDecision] | None = None,
    *,
    conflict_decisions: dict[str, ImportConflictDecision] | None = None,
) -> CollectionImportPlanResult:
    """Build the resulting collection list by applying decisions per conflict.

    Duplicate names *within* ``incoming`` itself (unrelated to any existing
    collection) are always renamed like a Keep Both outcome, with no prompt and
    no ``decisions`` lookup, since neither duplicate is a collection the user
    already had locally to protect.
    """
    if decisions is None and conflict_decisions is not None:
        decisions = conflict_decisions
    if decisions is None:
        decisions = {}
    result: list[Collection] = list(existing)
    existing_names = {col.name for col in existing}
    taken_collection_ids = {col.id for col in existing}
    taken_request_ids = {req.id for col in existing for req in col.requests}
    taken_ws_ids = {ws.id for col in existing for ws in getattr(col, "websockets", [])}

    added: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    renamed: list[tuple[str, str]] = []
    persisted: list[Collection] = []
    request_count = 0
    websocket_count = 0
    seen_incoming_names: set[str] = set()

    def keep_both(source: Collection, name: str) -> None:
        nonlocal request_count, websocket_count
        new_name = generate_import_copy_name(name, {col.name for col in result})
        new_col = _materialize(
            source, new_name, taken_collection_ids, taken_request_ids, taken_ws_ids
        )
        result.append(new_col)
        persisted.append(new_col)
        renamed.append((name, new_name))
        request_count += len(new_col.requests)
        websocket_count += len(getattr(new_col, "websockets", []))

    for source in incoming:
        name = source.name
        if name in seen_incoming_names:
            keep_both(source, name)
            continue
        seen_incoming_names.add(name)

        if name not in existing_names:
            new_col = _materialize(
                source, name, taken_collection_ids, taken_request_ids, taken_ws_ids
            )
            result.append(new_col)
            persisted.append(new_col)
            added.append(name)
            request_count += len(new_col.requests)
            websocket_count += len(getattr(new_col, "websockets", []))
            continue

        decision = decisions.get(name, ImportConflictDecision.SKIP)
        if decision is ImportConflictDecision.SKIP:
            skipped.append(name)
        elif decision is ImportConflictDecision.OVERWRITE:
            index = next(i for i, col in enumerate(result) if col.name == name)
            replaced = result[index]
            taken_request_ids.difference_update(req.id for req in replaced.requests)
            taken_ws_ids.difference_update(ws.id for ws in getattr(replaced, "websockets", []))
            new_requests = _reserve_requests(source.requests, taken_request_ids)
            new_websockets = _reserve_websockets(getattr(source, "websockets", []), taken_ws_ids)
            library_link = getattr(source, "library_link", None)
            result[index] = Collection(
                id=replaced.id,
                name=replaced.name,
                description=source.description,
                version=source.version,
                variables=[v.model_copy(deep=True) for v in getattr(source, "variables", [])],
                presets=dict(getattr(source, "presets", {})),
                requests=new_requests,
                websockets=new_websockets,
                mcp_clients=[
                    mcp.model_copy(deep=True) for mcp in getattr(source, "mcp_clients", [])
                ],
                library_link=(
                    library_link.model_copy(deep=True) if library_link is not None else None
                ),
            )
            persisted.append(result[index])
            updated.append(name)
            request_count += len(new_requests)
            websocket_count += len(new_websockets)
        elif decision is ImportConflictDecision.KEEP_BOTH:
            keep_both(source, name)

    logger.info(
        "collection_import_plan_created added=%d updated=%d skipped=%d "
        "renamed=%d requests=%d websockets=%d",
        len(added),
        len(updated),
        len(skipped),
        len(renamed),
        request_count,
        websocket_count,
    )
    return CollectionImportPlanResult(
        collections=result,
        persisted=persisted,
        added=added,
        updated=updated,
        skipped=skipped,
        renamed=renamed,
        request_count=request_count,
        parse_errors=[],
        websocket_count=websocket_count,
    )


def recount_collection_import_plan(
    plan: CollectionImportPlanResult,
    failed_ids: set[str],
) -> CollectionImportPlanResult:
    """Recount import plan counts to reflect only collections persisted to disk.

    Args:
        plan: The initial planned import result.
        failed_ids: Collection IDs that encountered OSError during save_collection.

    Returns:
        A new CollectionImportPlanResult with added, updated, renamed, and
        request_count adjusted to exclude failed collections.
    """
    if not failed_ids:
        return plan

    failed_persisted = [col for col in plan.persisted if col.id in failed_ids]
    succeeded_persisted = [col for col in plan.persisted if col.id not in failed_ids]

    failed_names = {col.name for col in failed_persisted}

    failed_renamed_pairs = {
        (orig, new_name)
        for orig, new_name in plan.renamed
        if new_name in failed_names
    }
    renamed = [pair for pair in plan.renamed if pair not in failed_renamed_pairs]

    failed_renamed_new_names = {new_name for _, new_name in failed_renamed_pairs}
    non_renamed_failed_names = failed_names - failed_renamed_new_names

    updated = [name for name in plan.updated if name not in non_renamed_failed_names]
    added = [name for name in plan.added if name not in non_renamed_failed_names]

    request_count = sum(len(col.requests) for col in succeeded_persisted)
    websocket_count = sum(len(getattr(col, "websockets", [])) for col in succeeded_persisted)

    logger.info(
        "collection_import_plan_recounted failed_count=%d persisted_collections=%d "
        "requests=%d websockets=%d",
        len(failed_ids),
        len(succeeded_persisted),
        request_count,
        websocket_count,
    )
    return CollectionImportPlanResult(
        collections=[col for col in plan.collections if col.id not in failed_ids],
        persisted=succeeded_persisted,
        added=added,
        updated=updated,
        skipped=list(plan.skipped),
        renamed=renamed,
        request_count=request_count,
        parse_errors=list(plan.parse_errors),
        websocket_count=websocket_count,
    )


def format_collection_import_result(result: CollectionImportPlanResult) -> str:
    """Human-readable summary for the import result dialog."""
    lines = [
        SUMMARY_COLLECTIONS_ADDED.format(count=len(result.added)),
        SUMMARY_COLLECTIONS_UPDATED.format(count=len(result.updated)),
        SUMMARY_COLLECTIONS_SKIPPED.format(count=len(result.skipped)),
        SUMMARY_COLLECTIONS_RENAMED.format(count=len(result.renamed)),
        SUMMARY_REQUESTS_IMPORTED.format(count=result.request_count),
        SUMMARY_WEBSOCKETS_IMPORTED.format(count=result.websocket_count),
    ]
    if result.renamed:
        lines.append("")
        lines.append(SUMMARY_RENAMED_HEADER)
        for original, new_name in result.renamed:
            lines.append(f'  "{original}" -> "{new_name}"')
    if result.parse_errors:
        lines.append("")
        lines.append(SUMMARY_ERRORS_HEADER)
        lines.extend(f"  {error}" for error in result.parse_errors)
    return "\n".join(lines)
