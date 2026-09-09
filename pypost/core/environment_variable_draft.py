"""Transactional working copy for the environment variable table."""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from pypost.core.environment_variable_validation import (
    EnvironmentVariableKeyValidation,
    validate_environment_variable_key,
)
from pypost.models.models import Environment


@dataclass
class EnvironmentVariableDraftRow:
    """One editable row with identity independent of its key or table position."""

    key: str = ""
    value: str = ""
    hidden: bool = False
    row_id: str = field(default_factory=lambda: str(uuid4()))


class EnvironmentVariableTableDraft:
    """Applies individual valid edits without reading back the whole Qt table."""

    def __init__(self, environment: Environment) -> None:
        self.rows = [
            EnvironmentVariableDraftRow(
                key=key,
                value=value,
                hidden=key in environment.hidden_keys,
            )
            for key, value in environment.variables.items()
        ]
        self._ensure_trailing_row()

    def row(self, index: int) -> EnvironmentVariableDraftRow | None:
        if 0 <= index < len(self.rows):
            return self.rows[index]
        return None

    def edit_key(
        self,
        index: int,
        proposed_name: str,
    ) -> EnvironmentVariableKeyValidation:
        row = self.rows[index]
        validation = validate_environment_variable_key(
            proposed_name,
            other_names=(other.key for i, other in enumerate(self.rows) if i != index),
        )
        if not validation.accepted:
            return validation
        row.key = validation.normalized_name
        self._ensure_trailing_row()
        return validation

    def edit_value(self, index: int, value: str) -> None:
        self.rows[index].value = value

    def edit_hidden(self, index: int, hidden: bool) -> None:
        self.rows[index].hidden = hidden

    def delete(self, index: int) -> EnvironmentVariableDraftRow | None:
        row = self.row(index)
        if row is None or not row.key:
            return None
        deleted = self.rows.pop(index)
        self._ensure_trailing_row()
        return deleted

    def move(self, index: int, direction: str) -> int | None:
        row = self.row(index)
        if row is None or not row.key or direction not in {"up", "down"}:
            return None
        populated_count = len(self.populated_rows)
        target = index - 1 if direction == "up" else index + 1
        if target < 0 or target >= populated_count:
            return None
        self.rows[index], self.rows[target] = self.rows[target], self.rows[index]
        return target

    @property
    def populated_rows(self) -> list[EnvironmentVariableDraftRow]:
        return [row for row in self.rows if row.key]

    def apply_to(self, environment: Environment) -> None:
        populated = self.populated_rows
        environment.variables = {row.key: row.value for row in populated}
        environment.hidden_keys = {row.key for row in populated if row.hidden}

    def _ensure_trailing_row(self) -> None:
        if not self.rows or self.rows[-1].key:
            self.rows.append(EnvironmentVariableDraftRow())
