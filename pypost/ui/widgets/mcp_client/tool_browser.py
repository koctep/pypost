"""Remote-tool list for the MCP Client workspace (name and description)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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

    tool_selected = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Remote tools", self))
        self._list = QListWidget(self)
        set_widget_id(self._list, MCP_CLIENT_TOOL_BROWSER)
        self._list.currentItemChanged.connect(self._on_current_item_changed)
        layout.addWidget(self._list)

    def set_tools(self, tools: list[tuple[str, str]]) -> None:
        """Replace rows. Each row shows name and description. Empty list is OK."""
        self._list.blockSignals(True)
        self._list.clear()
        for name, description in tools:
            label = name if not description else f"{name} - {description}"
            item = QListWidgetItem(label)
            item.setToolTip(description)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._list.addItem(item)
        self._list.blockSignals(False)

    def clear_tools(self) -> None:
        """Remove all discovered tool rows."""
        self._list.blockSignals(True)
        self._list.clear()
        self._list.blockSignals(False)

    def select_tool_by_name(self, name: str) -> None:
        """Select the row for ``name`` without emitting ``tool_selected``."""
        self._list.blockSignals(True)
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item is None:
                continue
            stored = item.data(Qt.ItemDataRole.UserRole)
            if stored == name:
                self._list.setCurrentRow(index)
                break
        self._list.blockSignals(False)

    def _on_current_item_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            self.tool_selected.emit(None)
            return
        stored = current.data(Qt.ItemDataRole.UserRole)
        if isinstance(stored, str) and stored:
            self.tool_selected.emit(stored)
            return
        self.tool_selected.emit(None)
