"""MCP Client draft headers table (empty-row key/value editor)."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from pypost.ui.widgets.empty_row_key_value_table import EmptyRowKeyValueTable

__all__ = ["McpClientHeadersTable"]


class McpClientHeadersTable(EmptyRowKeyValueTable):
    """Editable Key/Value headers table; strips keys on collect (FR-4)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, strip_keys=True)
