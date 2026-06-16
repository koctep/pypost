# PYPOST-721: Architecture

## Test Strategy

Each dialog gets its own test module, following `doc/dev/gui_testing.md` conventions:
module-scoped `qapp` fixture, dialog constructed and closed per test, no `pytest-qt`
dependency.

| Dialog | Test file | Key behaviors covered |
|--------|-----------|------------------------|
| `SaveRequestDialog` | `tests/test_save_dialog.py` | combo population, new-collection input visibility toggle, validation (empty name / empty collection name), accept paths for both new and existing collection |
| `McpActivityDialog` | `tests/test_mcp_activity_dialog.py` | empty vs populated summary text, table visibility/row count, `set_entries` re-population, module-level formatter functions |
| `McpToolsOverviewDialog` | `tests/test_mcp_tools_overview_dialog.py` | empty vs populated summary, table visibility, row content correctness |

## Key Technique: isHidden() vs isVisible()

Offscreen dialogs are never `show()`n, so Qt's `isVisible()` always returns `False`
(it requires the full ancestor chain to be visible). Tests instead assert on
`isHidden()`, which reflects only the widget's own explicit `show()`/`hide()` calls
made by the dialog's own logic — the correct signal for testing `setVisible()`-driven
behavior offscreen.
