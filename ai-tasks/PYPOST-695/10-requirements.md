# PYPOST-695: Elevate MainWindow service wiring to main.py

## Goals

Close architecture audit finding **R-P2-002** from PYPOST-684: move `StorageManager`,
`RequestManager`, and `MCPServerManager` construction from `MainWindow.__init__` to `main.py`
for parity with `TemplateService`, `ConfigManager`, and `HistoryManager`.

**Business intent:** Lower test-setup cost and align runtime wiring with documented
testability patterns — no user-visible behavior change.

## User Stories

- As a **developer**, I want storage/request/MCP services created once in `main.py`, so tests
  can inject mocks without patching `MainWindow` internals.
- As a **reviewer**, I want encryption policy applied before async collection/env loads start.

## Definition of Done

- `StorageManager`, `RequestManager`, `MCPServerManager` constructed in `main.py` and passed
  to `MainWindow`.
- `storage.apply_encryption_settings(settings)` called in `main.py` before UI startup loads.
- `MainWindow` accepts optional `storage`, `request_manager`, `mcp_manager` with fallbacks.
- `doc/dev/testability.md` and `doc/dev/architecture.md` updated.
- `make check` passes.

## Out of scope

- Elevating `StyleManager` or presenters (PYPOST-43).
- Changing persistence, MCP, or request execution behavior.

## Source

- Jira [PYPOST-695](https://pypost.atlassian.net/browse/PYPOST-695)
- Audit R-P2-002 in `ai-tasks/PYPOST-684/30-audit-report.md`
