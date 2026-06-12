# PYPOST-429: Technical Debt Analysis

## Resolved

- **TD-4 (Sprint 134 / PYPOST-403)**: Root cause of deleted ELF `core` dump investigated and
  documented in `ai-tasks/PYPOST-429/investigation-report.md`.

## Shortcuts Taken

None — documentation-only closure after unreproducible crash.

## Code Quality Issues

None blocking. Optional non-blocker noted below.

## Missing Tests

Not applicable — native segfault is not unit-testable without reproduction.

## Performance Concerns

None.

## Follow-ups

| Item | Severity | Jira | Notes |
| --- | --- | --- | --- |
| Migrate `TestOnRequestError` to pytest + `qapp` | Low | — | Reduces QApplication lifecycle footguns; not required for this closure |

No new Jira issues created — optional refactor is low priority and does not block release.

## Verdict

**SAFE TO CLOSE** — no blockers. Crash unreproducible; preventive `.gitignore` and offscreen Qt
already in place from PYPOST-403.
