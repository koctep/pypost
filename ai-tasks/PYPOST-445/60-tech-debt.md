# PYPOST-445: Technical Debt Analysis

## Shortcuts Taken

- None. Restart simulated via fresh `ConfigManager()` rather than full `MainWindow` bootstrap
  (adequate for persistence contract; MainWindow save uses the same API).

## Code Quality Issues

- None introduced.

## Missing Tests

- **Resolved:** Restart-level integration for `request_timeout` after SettingsDialog save —
  this task's deliverable.
- **Optional (non-blocker):** MainWindow-level test that `open_settings()` save + new
  `StateManager` load reflects timeout — low value given ConfigManager + dialog coverage.
- `StateManager` load reflects timeout — low value given ConfigManager + dialog coverage. — [PYPOST-626](https://pypost.atlassian.net/browse/PYPOST-626)

## Performance Concerns

- None. One additional offscreen Qt test with negligible runtime.

## Deviations from Architecture

- None. Implementation matches `20-architecture.md`.

## Documentation Debt

- None blocking. STEP 7 updates `doc/dev/settings_dialog.md`.

## Follow-up Tasks

No new follow-up Jira issues required. PYPOST-424 restart-test debt is closed by this task.

## Blocker Review Verdict

**SAFE TO CLOSE** — no blockers. Acceptance criteria met; tests pass; test-only scope with
no production regressions.
