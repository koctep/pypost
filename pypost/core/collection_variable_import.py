"""Pure domain engine for importing collection variables into workspace environments."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from typing import Any

from pypost.core.variable_name_validation import validate_variable_name
from pypost.models.models import Collection, Environment

logger = logging.getLogger(__name__)


class ConflictStrategy(str, Enum):
    """Conflict resolution policy when variable name already exists in target environment."""

    SKIP = "skip"
    OVERWRITE = "overwrite"


@dataclass
class ImportSummary:
    """Detailed summary of the environment variable import operation."""

    added_keys: list[str] = field(default_factory=list)
    updated_keys: list[str] = field(default_factory=list)
    skipped_keys: list[str] = field(default_factory=list)
    invalid_keys: list[tuple[str, str]] = field(default_factory=list)
    newly_hidden_keys: set[str] = field(default_factory=set)

    @property
    def total_imported(self) -> int:
        return len(self.added_keys) + len(self.updated_keys)

    def format_summary(self) -> str:
        parts: list[str] = []
        if self.added_keys:
            parts.append(f"{len(self.added_keys)} added")
        if self.updated_keys:
            parts.append(f"{len(self.updated_keys)} updated")
        if self.skipped_keys:
            parts.append(f"{len(self.skipped_keys)} skipped")
        if self.invalid_keys:
            parts.append(f"{len(self.invalid_keys)} invalid")
        summary_details = ", ".join(parts) if parts else "no variables imported"
        return f"Imported {self.total_imported} variable(s) ({summary_details})."


def format_variable_value(value: Any) -> str:
    """Normalize raw Python value to string for storage in Environment.variables."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def import_collection_variables_to_environment(
    environment: Environment,
    collection: Collection,
    conflict_strategy: ConflictStrategy = ConflictStrategy.SKIP,
    selected_keys: set[str] | None = None,
    preset_name: str | None = None,
) -> ImportSummary:
    """Import declared collection variables into the target environment.

    Args:
        environment: The destination working environment to mutate.
        collection: The source collection providing variable declarations and presets.
        conflict_strategy: Conflict policy for existing keys (SKIP or OVERWRITE).
        selected_keys: Optional set of variable names to selectively import.
            If None, all variables are imported.
        preset_name: Optional preset profile name to take values from instead of base defaults.

    Returns:
        ImportSummary detailing added, updated, skipped, invalid, and newly hidden variables.
    """
    strategy_val = (
        conflict_strategy.value
        if hasattr(conflict_strategy, "value")
        else str(conflict_strategy)
    )
    selected_count_str = str(len(selected_keys)) if selected_keys is not None else "all"
    logger.info(
        "collection_variable_import_started env_name=%s collection_name=%s preset=%s "
        "conflict_strategy=%s selected_keys_count=%s",
        environment.name,
        collection.name,
        preset_name,
        strategy_val,
        selected_count_str,
    )
    summary = ImportSummary()

    try:
        preset_values: dict[str, Any] = {}
        if preset_name and collection.presets:
            preset_values = collection.presets.get(preset_name, {})

        variables = collection.variables or []
        for var in variables:
            if selected_keys is not None and var.name not in selected_keys:
                continue

            is_valid, error_msg = validate_variable_name(var.name)
            if not is_valid:
                logger.warning(
                    "collection_variable_import_invalid_key env_name=%s collection_name=%s "
                    "key=%s error=%s",
                    environment.name,
                    collection.name,
                    var.name,
                    error_msg,
                )
                summary.invalid_keys.append((var.name, error_msg))
                continue

            raw_val = preset_values.get(var.name, var.default)
            val_str = format_variable_value(raw_val)

            if var.name in environment.variables:
                if conflict_strategy == ConflictStrategy.OVERWRITE:
                    environment.variables[var.name] = val_str
                    summary.updated_keys.append(var.name)
                    action = "updated"
                else:
                    summary.skipped_keys.append(var.name)
                    action = "skipped"
            else:
                environment.variables[var.name] = val_str
                summary.added_keys.append(var.name)
                action = "added"

            if var.secret:
                if var.name not in environment.hidden_keys:
                    summary.newly_hidden_keys.add(var.name)
                    environment.hidden_keys.add(var.name)
                environment.mcp_overridable_keys.discard(var.name)

            logger.debug(
                "collection_variable_import_key_evaluated env_name=%s collection_name=%s "
                "key=%s is_secret=%s action=%s",
                environment.name,
                collection.name,
                var.name,
                bool(var.secret),
                action,
            )

        logger.info(
            "collection_variable_import_completed env_name=%s collection_name=%s "
            "total=%d added=%d updated=%d skipped=%d invalid=%d newly_hidden=%d",
            environment.name,
            collection.name,
            summary.total_imported,
            len(summary.added_keys),
            len(summary.updated_keys),
            len(summary.skipped_keys),
            len(summary.invalid_keys),
            len(summary.newly_hidden_keys),
        )
        return summary
    except Exception as exc:
        logger.error(
            "collection_variable_import_failed env_name=%s collection_name=%s error=%s",
            environment.name,
            collection.name,
            exc,
            exc_info=True,
        )
        raise
