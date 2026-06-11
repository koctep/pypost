# PYPOST-464: Technical Debt Analysis

## Shortcuts Taken

No significant shortcuts. Tests use real `MetricsManager` and `RequestService` with HTTP and
history manager mocked at boundaries — matching the architecture plan and repo conventions.

## Code Quality Issues

- Helper functions (`_scrape_metrics`, `_execute_request`) are local to the test module. No shared
  extraction was needed; duplicating the small scrape helper matches `test_storage_environments.py`.
- Mock-based metric tests in `tests/test_request_service.py` remain alongside scrape tests; both
  provide value (fast unit vs registry integration).

## Missing Tests

- **Closed by this task:** explicit Prometheus scrape tests for `hidden_value_masks_applied_total`
  with empty vs non-empty `hidden_keys` (debt item from PYPOST-446).
- **Still open (out of scope):**
  - Refactor `RequestService` history-recording block — [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463).
  - Full MainWindow click-through automation — not required.
  - Full-project regression in CI — [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465).

## Performance Concerns

None introduced. Three isolated tests each construct a fresh `MetricsManager` and perform one
mocked HTTP execute.

## Follow-up Tasks

None filed from PYPOST-464. Remaining debt items are already tracked in sibling tickets:

- Refactor `RequestService` history-recording block:
  [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463)
- CI/local dependency provisioning for full regression:
  [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465)

## Blocker Review

**Verdict: SAFE TO CLOSE**

All acceptance criteria met. No blockers identified.
