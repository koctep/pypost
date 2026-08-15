"""Pure logic for exporting environments to a file (PYPOST-988).

No Qt dependency: scope selection, payload shaping, and file writing are
directly unit-testable without a QApplication. Qt-facing dialogs live in
``pypost.ui.collection_item_dialogs``; orchestration lives in
``EnvironmentListWidget.export_environments``.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pypost.core.export_file_writer import write_json_export_file
from pypost.core.json_export_root import json_root_for_records
from pypost.core.storage_interface import StorageInterface
from pypost.models.models import Environment

logger = logging.getLogger(__name__)

__all__ = [
    "EnvironmentExportError",
    "ExportPlanResult",
    "ExportScope",
    "build_export_payload",
    "environments_for_export",
    "export_includes_hidden",
    "format_export_result",
    "suggested_export_filename",
    "write_export_file",
]


class EnvironmentExportError(Exception):
    """Raised when an export file cannot be written."""


class ExportScope(str, Enum):
    """Which environments the user chose to export."""

    SELECTED = "selected"
    ALL = "all"


@dataclass(frozen=True)
class ExportPlanResult:
    """Summary of a completed export."""

    exported_count: int
    environment_names: list[str]
    includes_hidden: bool
    path: Path


def environments_for_export(
    all_environments: list[Environment],
    *,
    scope: ExportScope,
    selected_index: int | None,
) -> list[Environment]:
    """Return the environments to export for the chosen scope."""
    if scope is ExportScope.ALL:
        return list(all_environments)
    if selected_index is None or selected_index < 0:
        return []
    if selected_index >= len(all_environments):
        return []
    return [all_environments[selected_index]]


def export_includes_hidden(environments: list[Environment]) -> bool:
    """True when any environment to export has at least one Hidden variable."""
    return any(env.hidden_keys for env in environments)


def suggested_export_filename(environments: list[Environment]) -> str:
    """Default save-dialog filename for the export payload shape."""
    if len(environments) == 1:
        safe_name = environments[0].name.strip() or "environment"
        for char in '\\/:*?"<>|':
            safe_name = safe_name.replace(char, "_")
        return f"{safe_name}.json"
    return "environments.json"


def build_export_payload(
    environments: list[Environment],
    storage: StorageInterface,
) -> list[dict] | dict:
    """Serialize environments into native PyPost JSON import shape.

    A single environment is exported as one JSON object; multiple environments
    are exported as a JSON list — both shapes are accepted by import.
    """
    records = storage.serialize_environment_records(environments)
    logger.info(
        "environment_export_payload_built count=%d includes_hidden=%s",
        len(environments),
        export_includes_hidden(environments),
    )
    return json_root_for_records(records)


def write_export_file(path: Path, payload: list[dict] | dict) -> None:
    """Write the export payload to ``path`` as indented UTF-8 JSON."""
    write_json_export_file(path, payload, error_cls=EnvironmentExportError)
    logger.info("environment_export_file_written path=%s", path)


def format_export_result(result: ExportPlanResult) -> str:
    """Human-readable summary for the export result dialog."""
    names = ", ".join(f'"{name}"' for name in result.environment_names)
    lines = [
        f"Exported {result.exported_count} environment(s) to:",
        str(result.path),
        "",
        f"Environments: {names}",
    ]
    if result.includes_hidden:
        lines.append("")
        lines.append(
            "The file may contain Hidden variable values. Store and share it "
            "carefully."
        )
    return "\n".join(lines)
