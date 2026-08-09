"""Pure logic for importing environments from a file (PYPOST-986).

No Qt dependency: parsing, conflict detection, naming, and planning are all
directly unit-testable without a QApplication. Qt-facing dialogs live in
``pypost.ui.collection_item_dialogs``; orchestration lives in
``EnvironmentListWidget.import_environments``.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pypost.core.environment_ops import clone_environment
from pypost.core.import_conflicts import ImportConflictDecision, generate_import_copy_name
from pypost.core.storage_interface import StorageInterface
from pypost.models.models import Environment

logger = logging.getLogger(__name__)

__all__ = [
    "EnvironmentImportFileError",
    "ImportConflictDecision",
    "ImportPlanResult",
    "find_conflicts",
    "format_import_result",
    "generate_import_copy_name",
    "load_import_candidates",
    "plan_import",
]


class EnvironmentImportFileError(Exception):
    """Raised for unreadable, malformed, or wrong-shaped import files."""


@dataclass(frozen=True)
class ImportPlanResult:
    """The outcome of planning an import: the new target list plus a summary."""

    environments: list[Environment]
    added: list[str]
    updated: list[str]
    skipped: list[str]
    renamed: list[tuple[str, str]]
    parse_errors: list[str]


def load_import_candidates(
    path: Path, storage: StorageInterface
) -> tuple[list[Environment], list[str]]:
    """Read and parse an import file into candidate environments.

    Accepts either a JSON list of environment records or a single JSON object
    (normalized to a one-item list), matching what a hand-shared file or a
    copy of ``environments.json`` can realistically look like.

    Raises:
        EnvironmentImportFileError: for file-level problems only (unreadable
            file, malformed JSON, or a root shape that is neither a list nor
            an object). Per-record failures (e.g. an undecryptable hidden
            value) are reported via the returned ``parse_errors`` instead, so
            one bad entry never blocks the rest of the file.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EnvironmentImportFileError(f"Could not read file: {exc}") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnvironmentImportFileError(f"File is not valid JSON: {exc}") from exc

    if isinstance(data, dict):
        records = [data]
    elif isinstance(data, list):
        records = data
    else:
        raise EnvironmentImportFileError(
            "File must contain a JSON object or a list of environment objects."
        )

    if not all(isinstance(item, dict) for item in records):
        raise EnvironmentImportFileError(
            "Each environment entry in the file must be a JSON object."
        )

    environments, failures = storage.deserialize_environment_records(records)
    parse_errors = [failure.format_operator_message() for failure in failures]
    logger.info(
        "environment_import_file_parsed path=%s candidate_count=%d error_count=%d",
        path,
        len(environments),
        len(parse_errors),
    )
    return environments, parse_errors


def find_conflicts(existing: list[Environment], incoming: list[Environment]) -> list[str]:
    """Names present in both lists, in incoming order, without duplicates."""
    existing_names = {env.name for env in existing}
    conflicts: list[str] = []
    seen: set[str] = set()
    for env in incoming:
        if env.name in existing_names and env.name not in seen:
            conflicts.append(env.name)
            seen.add(env.name)
    return conflicts


def plan_import(
    existing: list[Environment],
    incoming: list[Environment],
    decisions: dict[str, ImportConflictDecision],
) -> ImportPlanResult:
    """Build the resulting environment list by applying decisions per conflict.

    Duplicate names *within* ``incoming`` itself (unrelated to any existing
    environment) are always renamed like a Keep Both outcome, with no prompt
    and no ``decisions`` lookup, since neither duplicate is an environment the
    user already had locally to protect.
    """
    result_environments = list(existing)
    existing_names = {env.name for env in existing}
    added: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    renamed: list[tuple[str, str]] = []
    seen_incoming_names: set[str] = set()

    def current_names() -> set[str]:
        return {env.name for env in result_environments}

    for env in incoming:
        name = env.name
        if name in seen_incoming_names:
            new_name = generate_import_copy_name(name, current_names())
            result_environments.append(clone_environment(env, new_name))
            renamed.append((name, new_name))
            continue
        seen_incoming_names.add(name)

        if name not in existing_names:
            result_environments.append(env)
            added.append(name)
            continue

        decision = decisions.get(name, ImportConflictDecision.SKIP)
        if decision is ImportConflictDecision.SKIP:
            skipped.append(name)
        elif decision is ImportConflictDecision.OVERWRITE:
            index = next(i for i, e in enumerate(result_environments) if e.name == name)
            existing_env = result_environments[index]
            result_environments[index] = Environment(
                id=existing_env.id,
                name=existing_env.name,
                variables=dict(env.variables),
                hidden_keys=set(env.hidden_keys),
                enable_mcp=env.enable_mcp,
            )
            updated.append(name)
        elif decision is ImportConflictDecision.KEEP_BOTH:
            new_name = generate_import_copy_name(name, current_names())
            result_environments.append(clone_environment(env, new_name))
            renamed.append((name, new_name))

    return ImportPlanResult(
        environments=result_environments,
        added=added,
        updated=updated,
        skipped=skipped,
        renamed=renamed,
        parse_errors=[],
    )


def format_import_result(result: ImportPlanResult) -> str:
    """Human-readable summary for the import result dialog."""
    lines = [
        f"Added: {len(result.added)}",
        f"Updated: {len(result.updated)}",
        f"Skipped: {len(result.skipped)}",
        f"Renamed: {len(result.renamed)}",
    ]
    if result.renamed:
        lines.append("")
        lines.append("Renamed on import:")
        for original, new_name in result.renamed:
            lines.append(f'  "{original}" -> "{new_name}"')
    if result.parse_errors:
        lines.append("")
        lines.append("Entries that failed to import:")
        lines.extend(f"  {error}" for error in result.parse_errors)
    return "\n".join(lines)
