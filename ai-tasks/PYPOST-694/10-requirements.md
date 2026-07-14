# PYPOST-694: Inject HistoryManager from composition root

## Goals

Close architecture audit finding **R-P2-001 (S-HIST-003)** from PYPOST-684: move
`HistoryManager` construction from `MainWindow.__init__` to `main.py` so production uses a
single shared instance injected through the composition root, matching
`ConfigManager`, `TemplateService`, and `AlertManager`.

**Business intent:** Lower test-setup cost and align runtime wiring with documented
testability patterns — no user-visible behavior change.

## User Stories

- As a **developer**, I want `HistoryManager` created once in `main.py`, so tests can inject
  a mock or temp-path instance without patching `MainWindow` internals.
- As a **reviewer**, I want `testability.md` to list `HistoryManager` in the composition-root
  table, so audit finding S-HIST-003 is resolved.

## Definition of Done

- `HistoryManager()` constructed in `main.py` and passed to `MainWindow`.
- `MainWindow` accepts optional `history_manager` with fallback when omitted (test convenience).
- `doc/dev/testability.md` composition-root and MainWindow injection tables updated.
- MainWindow test helpers use constructor injection instead of `patch(HistoryManager)`.
- `make check` passes.

## Out of scope

- Elevating `StorageManager`, `RequestManager`, or `MCPServerManager` (PYPOST-695).
- Changing history persistence format, masking, or UI behavior.

## Source

- Jira [PYPOST-694](https://pypost.atlassian.net/browse/PYPOST-694)
- Audit R-P2-001 in `ai-tasks/PYPOST-684/30-audit-report.md`
