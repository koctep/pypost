"""Blank MCP Client workspace page (placeholder until PYPOST-1166)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pypost.ui.widget_ids import MCP_CLIENT_TAB_PAGE, set_widget_id

__all__ = ["McpClientTab"]


class McpClientTab(QWidget):
    """Blank MCP Client workspace page (placeholder until PYPOST-1166)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_widget_id(self, MCP_CLIENT_TAB_PAGE)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("MCP Client", self))
