"""Snapshot of active environment variables for MCP supplier callbacks."""
from __future__ import annotations


class EnvVariableSnapshot:
    """Holds a copy of env vars and hidden keys updated on the main thread."""

    def __init__(self) -> None:
        self._variables: dict[str, str] = {}
        self._hidden_keys: set[str] = set()

    def update(
        self,
        variables: dict[str, str],
        hidden_keys: set[str] | None = None,
    ) -> None:
        self._variables = dict(variables)
        self._hidden_keys = set(hidden_keys or ())

    def snapshot_variables(self) -> dict[str, str]:
        return dict(self._variables)

    def snapshot_hidden_keys(self) -> set[str]:
        return set(self._hidden_keys)
