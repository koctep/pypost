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
import uuid
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from pypost.core.collection_messages import (
    MSG_ENTRY_MISSING_NAME,
    MSG_ENTRY_REQUESTS_NOT_LIST,
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
    format_collection_entry_error,
    format_unnamed_entry_label,
)
from pypost.core.import_conflicts import ImportConflictDecision, generate_import_copy_name
from pypost.models.models import Collection, RequestData

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
    renamed: dict[str, str]
    request_count: int
    parse_errors: list[str]


def _read_records(path: Path) -> list[dict]:
    """Read the file and normalize its JSON root into a list of records."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CollectionImportFileError(MSG_FILE_UNREADABLE.format(reason=exc)) from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
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
    return None


def load_collection_import_candidates(path: Path) -> tuple[list[Collection], list[str]]:
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

    collections: list[Collection] = []
    parse_errors: list[str] = []
    for index, record in enumerate(records, start=1):
        label = _record_label(record, index)
        shape_error = _shape_error(record)
        if shape_error is not None:
            parse_errors.append(format_collection_entry_error(label, shape_error))
            continue
        try:
            collections.append(Collection(**record))
        except ValidationError as exc:
            parse_errors.append(format_collection_entry_error(label, str(exc)))

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


def _materialize(
    source: Collection,
    name: str,
    taken_collection_ids: set[str],
    taken_request_ids: set[str],
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
    return Collection(
        id=collection_id,
        name=name,
        requests=_reserve_requests(source.requests, taken_request_ids),
    )


def plan_collection_import(
    existing: list[Collection],
    incoming: list[Collection],
    decisions: dict[str, ImportConflictDecision],
) -> CollectionImportPlanResult:
    """Build the resulting collection list by applying decisions per conflict.

    Duplicate names *within* ``incoming`` itself (unrelated to any existing
    collection) are always renamed like a Keep Both outcome, with no prompt and
    no ``decisions`` lookup, since neither duplicate is a collection the user
    already had locally to protect.
    """
    result: list[Collection] = list(existing)
    existing_names = {col.name for col in existing}
    taken_collection_ids = {col.id for col in existing}
    taken_request_ids = {req.id for col in existing for req in col.requests}

    added: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    renamed: dict[str, str] = {}
    persisted: list[Collection] = []
    request_count = 0
    seen_incoming_names: set[str] = set()

    def keep_both(source: Collection, name: str) -> None:
        nonlocal request_count
        new_name = generate_import_copy_name(name, {col.name for col in result})
        new_col = _materialize(source, new_name, taken_collection_ids, taken_request_ids)
        result.append(new_col)
        persisted.append(new_col)
        renamed[name] = new_name
        request_count += len(new_col.requests)

    for source in incoming:
        name = source.name
        if name in seen_incoming_names:
            keep_both(source, name)
            continue
        seen_incoming_names.add(name)

        if name not in existing_names:
            new_col = _materialize(source, name, taken_collection_ids, taken_request_ids)
            result.append(new_col)
            persisted.append(new_col)
            added.append(name)
            request_count += len(new_col.requests)
            continue

        decision = decisions.get(name, ImportConflictDecision.SKIP)
        if decision is ImportConflictDecision.SKIP:
            skipped.append(name)
        elif decision is ImportConflictDecision.OVERWRITE:
            index = next(i for i, col in enumerate(result) if col.name == name)
            replaced = result[index]
            taken_request_ids.difference_update(req.id for req in replaced.requests)
            new_requests = _reserve_requests(source.requests, taken_request_ids)
            result[index] = Collection(
                id=replaced.id,
                name=replaced.name,
                requests=new_requests,
            )
            persisted.append(result[index])
            updated.append(name)
            request_count += len(new_requests)
        elif decision is ImportConflictDecision.KEEP_BOTH:
            keep_both(source, name)

    return CollectionImportPlanResult(
        collections=result,
        persisted=persisted,
        added=added,
        updated=updated,
        skipped=skipped,
        renamed=renamed,
        request_count=request_count,
        parse_errors=[],
    )


def format_collection_import_result(result: CollectionImportPlanResult) -> str:
    """Human-readable summary for the import result dialog."""
    lines = [
        SUMMARY_COLLECTIONS_ADDED.format(count=len(result.added)),
        SUMMARY_COLLECTIONS_UPDATED.format(count=len(result.updated)),
        SUMMARY_COLLECTIONS_SKIPPED.format(count=len(result.skipped)),
        SUMMARY_COLLECTIONS_RENAMED.format(count=len(result.renamed)),
        SUMMARY_REQUESTS_IMPORTED.format(count=result.request_count),
    ]
    if result.renamed:
        lines.append("")
        lines.append(SUMMARY_RENAMED_HEADER)
        for original, new_name in result.renamed.items():
            lines.append(f'  "{original}" -> "{new_name}"')
    if result.parse_errors:
        lines.append("")
        lines.append(SUMMARY_ERRORS_HEADER)
        lines.extend(f"  {error}" for error in result.parse_errors)
    return "\n".join(lines)
