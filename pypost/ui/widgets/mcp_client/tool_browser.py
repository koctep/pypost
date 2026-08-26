"""Remote-tool list for the MCP Client workspace (name and description)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pypost.ui.widget_ids import MCP_CLIENT_TOOL_BROWSER, set_widget_id

__all__ = ["McpClientToolBrowser"]


class McpClientToolBrowser(QWidget):
    """List of discovered remote MCP tools (name and description)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Remote tools", self))
        self._list = QListWidget(self)
        set_widget_id(self._list, MCP_CLIENT_TOOL_BROWSER)
        layout.addWidget(self._list)

    def set_tools(self, tools: list[tuple[str, str]]) -> None:
        """Replace rows. Each row shows name and description. Empty list is OK."""
        self._list.clear()
        for name, description in tools:
            label = name if not description else f"{name} - {description}"
            item = QListWidgetItem(label)
            item.setToolTip(description)
            self._list.addItem(item)

    def clear_tools(self) -> None:
        """Remove all discovered tool rows."""
        self._list.clear()
