# PYPOST-693: Technical Debt Analysis

## Shortcuts Taken

None. The remediation is a structural package split (file moves + import updates) with no
behavioral shortcuts.

## Code Quality Issues

None introduced. The `core/qt/` subpackage makes PySide6 coupling explicit and grep-verifiable.

## Missing Tests

No missing tests for this task's scope. All existing worker, gateway, MCP, metrics, and
storage tests were updated to import from `pypost.core.qt.*` and pass unchanged.

## Performance Concerns

None. Threading model, signal delivery, and gateway coalescing semantics are unchanged.

## Follow-up Tasks

Out-of-scope items from the audit, already tracked in Jira:

- [PYPOST-696, Medium] Relocate `request_sync.is_tab_dirty` tab-aware dirty-check helper
- [PYPOST-694, Medium] Move `HistoryManager` to composition root
- [PYPOST-695, Medium] Partial composition root in `MainWindow`
- [PYPOST-698, Medium] Allow `RequestService` injection in `RequestWorker`

No new follow-up issues required for PYPOST-693.
