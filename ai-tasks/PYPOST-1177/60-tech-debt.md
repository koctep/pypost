# PYPOST-1177: Technical Debt Analysis

## Shortcuts Taken

None. The fix applies the existing sibling `TestMainWindow` isolation pattern without introducing new compromises.

## Code Quality Issues

None introduced. `test_main_window_curl_copied_status_bar` now matches the module's established mock/patch boundaries documented in `20-architecture.md`.

## Missing Tests

None. Signal wiring remains covered by:

- `tests/test_main_window.py::TestMainWindow::test_main_window_curl_copied_status_bar` (integration: real `_build_layout` + `wire_presenter_signals`)
- `tests/test_main_window_signals.py::test_wire_presenter_signals_connects_curl_copied_status_bar` (unit)

## Performance Concerns

None.

## Follow-up Tasks

| Priority | Item | Notes |
| --- | --- | --- |
| — | PYPOST-1177 parallel Qt crash in `test_main_window_curl_copied_status_bar` | **Resolved** by this task (was NON-BLOCKER in [PYPOST-1176](../PYPOST-1176/60-tech-debt.md)) |
| NON-BLOCKER | Flaky parallel failures in MCP registry / WS lifecycle tests | Pre-existing from [PYPOST-1176](../PYPOST-1176/60-tech-debt.md); out of scope for PYPOST-1177 |

No new follow-up Jira issues required from this task.
