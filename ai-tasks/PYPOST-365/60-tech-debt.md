# PYPOST-365: Technical Debt Analysis

## Shortcuts Taken

- **Widget-level only**: Search tests drive `ResponseView` in isolation, not through
  `RequestTab` / `MainWindow`. Acceptable for PYPOST-37 search coverage; full tab integration
  remains optional.

## Code Quality Issues

- **Duplicate `qapp` fixtures**: Older GUI modules still define local `qapp`; conftest now
  provides a shared fixture for new tests. Migrating all modules is deferred (low priority).

## Missing Tests

- Keyboard shortcut Ctrl+F focus (not covered; low risk).
- Search debounce and large-document performance (PYPOST-363 / PYPOST-364 — separate tasks).

## Performance Concerns

None introduced; tests use small plain-text bodies.

## Follow-up Tasks

- **Consolidate `qapp` fixtures** (NON-BLOCKER): Remove duplicate module-level `qapp` from GUI
  test files once a dedicated cleanup task is scheduled.
- **MainWindow search integration** (NON-BLOCKER): Optional e2e if search is wired through tab
  lifecycle in future refactors.

## Blocker Review Verdict

**SAFE TO CLOSE** — acceptance criteria met; follow-ups are non-blocking.
