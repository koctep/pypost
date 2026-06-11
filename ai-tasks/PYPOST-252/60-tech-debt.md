# PYPOST-252: Technical Debt Analysis

## Shortcuts Taken

- **Debounced save race guard untested:** `StateManager._on_debounced_save_timeout` early return
  when `_save_pending` is already false (line 79) is not exercised — requires timer firing
  after synchronous `save()`; low risk defensive branch.

## Code Quality Issues

- None blocking.

## Missing Tests

- **MainWindow + real managers integration:** Presenters and integration tests use
  `FakeRequestManager` / `FakeStateManager`; full wiring is covered indirectly via
  `test_save_flow_integration.py`, `test_collections_presenter.py`, etc. Dedicated
  MainWindow↔manager E2E is out of scope for this debt ticket.

## Performance Concerns

- None — manager unit tests complete in under one second.

## Follow-up Tasks

- None required to close PYPOST-252.

## Blocker Review

**Verdict: SAFE TO CLOSE** — pytest infrastructure exists and is documented; RequestManager and
StateManager have adequate unit test coverage with edge-case gaps filled.
