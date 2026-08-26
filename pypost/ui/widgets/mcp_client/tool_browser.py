"""Empty remote-tool placeholder for the MCP Client draft shell (MCP-TM-3 fills)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from pypost.ui.widget_ids import MCP_CLIENT_TOOL_BROWSER, set_widget_id

__all__ = ["McpClientToolBrowser"]


class McpClientToolBrowser(QWidget):
    """Empty list reserved for discovered remote MCP tools."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Remote tools", self))
        self._list = QListWidget(self)
        set_widget_id(self._list, MCP_CLIENT_TOOL_BROWSER)
        layout.addWidget(self._list)
