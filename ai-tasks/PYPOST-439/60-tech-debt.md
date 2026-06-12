# PYPOST-439: Technical Debt Analysis

## Shortcuts Taken

None for acceptance criteria. Auth clear uses an explicit checkbox rather than a separate
settings workflow.

## Code Quality Issues

None introduced.

## Missing Tests (follow-up, non-blocking)

| Item | Priority | Notes |
| --- | --- | --- |
| E2E: Settings save → `settings.json` round-trip for alert fields | Low | Covered indirectly by dialog accept tests | [PYPOST-620](https://pypost.atlassian.net/browse/PYPOST-620) |
| Main window reload of `AlertManager` after settings save | Medium | Pre-existing gap | [PYPOST-621](https://pypost.atlassian.net/browse/PYPOST-621) |

## Performance Concerns

None.

## Follow-up Tasks

| Item | Priority | Notes |
| --- | --- | --- |
| Rebuild or reconfigure `AlertManager` when alert settings change | Medium | `MainWindow.apply_settings` does not touch `_alert_manager` today | [PYPOST-622](https://pypost.atlassian.net/browse/PYPOST-622) |

## Blocker Review Verdict

**SAFE TO CLOSE** — alert fields exposed with masked auth; tests pass; no security regression
in UI display of webhook authorization.
