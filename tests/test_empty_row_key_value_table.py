"""Shared EmptyRowKeyValueTable contracts (PYPOST-1186).

Asserts shared ancestry, FR-5 MCP decoupling from request_editor, and
strip / set_read_only / empty-row policies for HTTP, WebSocket, and MCP.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QAbstractItemView, QTableWidgetItem

pytestmark = pytest.mark.timeout(30)

_SHARED_MODULE = "pypost.ui.widgets.empty_row_key_value_table"
_REQUEST_EDITOR = "pypost.ui.widgets.request_editor"
_MCP_HEADERS = "pypost.ui.widgets.mcp_client.headers_table"
_MCP_TAB = "pypost.ui.widgets.mcp_client.mcp_client_tab"


def _imported_modules(source_path: Path) -> set[str]:
    """Return absolute-ish module names referenced by Import/ImportFrom nodes."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _module_file(module_name: str) -> Path:
    mod = importlib.import_module(module_name)
    assert mod.__file__ is not None
    return Path(mod.__file__)


def test_empty_row_key_value_table_shared_module_exports_type(qapp) -> None:
    """Shared EmptyRowKeyValueTable must live in the neutral widgets module."""
    mod = importlib.import_module(_SHARED_MODULE)
    cls = getattr(mod, "EmptyRowKeyValueTable", None)
    assert cls is not None, (
        f"{_SHARED_MODULE} must export EmptyRowKeyValueTable"
    )
    table = cls()
    assert table.columnCount() == 2
    assert table.rowCount() >= 1


def test_http_ws_mcp_tables_share_empty_row_key_value_ancestry(qapp) -> None:
    """HTTP, WS, and MCP Key/Value tables must share EmptyRowKeyValueTable."""
    from pypost.ui.widgets.empty_row_key_value_table import EmptyRowKeyValueTable
    from pypost.ui.widgets.mcp_client.headers_table import McpClientHeadersTable
    from pypost.ui.widgets.request_editor import KeyValueTable
    from pypost.ui.widgets.websocket.connection_editor import (
        WebSocketKeyValueTable,
    )

    for name, cls in (
        ("KeyValueTable", KeyValueTable),
        ("WebSocketKeyValueTable", WebSocketKeyValueTable),
        ("McpClientHeadersTable", McpClientHeadersTable),
    ):
        assert issubclass(cls, EmptyRowKeyValueTable), (
            f"{name} must be EmptyRowKeyValueTable or a subclass "
            f"(got MRO={[c.__name__ for c in cls.__mro__]})"
        )


def test_mcp_headers_and_tab_do_not_import_request_editor() -> None:
    """FR-5: mcp_client headers/tab must not import request_editor."""
    for module_name in (_MCP_HEADERS, _MCP_TAB):
        imports = _imported_modules(_module_file(module_name))
        assert _REQUEST_EDITOR not in imports, (
            f"{module_name} must not import {_REQUEST_EDITOR} (FR-5); "
            f"found imports={sorted(imports)}"
        )
        assert not any(
            name == "request_editor" or name.endswith(".request_editor")
            for name in imports
        ), (
            f"{module_name} must not import request_editor (FR-5); "
            f"found imports={sorted(imports)}"
        )

    headers = importlib.import_module(_MCP_HEADERS)
    assert _REQUEST_EDITOR not in headers.__dict__
    assert "request_editor" not in headers.__dict__


def test_http_get_data_preserves_unstripped_key(qapp) -> None:
    """HTTP KeyValueTable keeps raw keys (no strip) — strip_keys=False policy."""
    from pypost.ui.widgets.request_editor import KeyValueTable

    table = KeyValueTable()
    table.setItem(0, 0, QTableWidgetItem("  x"))
    table.setItem(0, 1, QTableWidgetItem("v"))
    data = table.get_data()
    assert "  x" in data
    assert data["  x"] == "v"
    assert "x" not in data


def test_ws_get_data_strips_keys_and_omits_whitespace_only(qapp) -> None:
    """WS get_data strips keys and drops whitespace-only names."""
    from pypost.ui.widgets.websocket.connection_editor import (
        WebSocketKeyValueTable,
    )

    table = WebSocketKeyValueTable()
    table.setItem(0, 0, QTableWidgetItem("  Auth  "))
    table.setItem(0, 1, QTableWidgetItem("token"))
    last = table.rowCount() - 1
    table.setItem(last, 0, QTableWidgetItem("   "))
    table.setItem(last, 1, QTableWidgetItem("ignored"))
    data = table.get_data()
    assert data == {"Auth": "token"}


def test_mcp_get_data_strips_keys_and_omits_whitespace_only(qapp) -> None:
    """MCP get_data strips keys and drops whitespace-only names."""
    from pypost.ui.widgets.mcp_client.headers_table import McpClientHeadersTable

    table = McpClientHeadersTable()
    table.setItem(0, 0, QTableWidgetItem("  Auth  "))
    table.setItem(0, 1, QTableWidgetItem("token"))
    last = table.rowCount() - 1
    table.setItem(last, 0, QTableWidgetItem("   "))
    table.setItem(last, 1, QTableWidgetItem("ignored"))
    data = table.get_data()
    assert data == {"Auth": "token"}


def test_ws_set_read_only_toggles_edit_triggers(qapp) -> None:
    """WS set_read_only(True) disables edits; False restores them."""
    from pypost.ui.widgets.websocket.connection_editor import (
        WebSocketKeyValueTable,
    )

    table = WebSocketKeyValueTable()
    table.set_read_only(True)
    assert table.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers
    table.set_read_only(False)
    restored = table.editTriggers()
    assert restored != QAbstractItemView.EditTrigger.NoEditTriggers
    assert bool(
        restored
        & (
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
    )


def test_shared_empty_row_grows_when_last_key_edited(qapp) -> None:
    """Typing in the last-row Key cell on the shared type appends a blank row."""
    from pypost.ui.widgets.empty_row_key_value_table import EmptyRowKeyValueTable

    table = EmptyRowKeyValueTable()
    last = table.rowCount() - 1
    assert last >= 0
    table.setItem(last, 0, QTableWidgetItem("Authorization"))
    table.setItem(last, 1, QTableWidgetItem("Bearer {{token}}"))
    assert table.rowCount() == last + 2
    assert table.get_data()["Authorization"] == "Bearer {{token}}"


def test_mcp_headers_imports_shared_empty_row_module_only_for_table() -> None:
    """After extract, MCP headers must import the shared module (not request_editor)."""
    imports = _imported_modules(_module_file(_MCP_HEADERS))
    assert _SHARED_MODULE in imports, (
        f"{_MCP_HEADERS} must import {_SHARED_MODULE} for the shared table type"
    )
    assert _REQUEST_EDITOR not in imports
    # Shared module must be loadable and not pull request_editor either.
    before = _REQUEST_EDITOR in sys.modules
    importlib.import_module(_SHARED_MODULE)
    if not before:
        # If request_editor was not loaded before, shared import must not load it.
        assert _REQUEST_EDITOR not in sys.modules
