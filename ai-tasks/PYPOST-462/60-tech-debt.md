# PYPOST-462: Technical Debt Analysis

## Shortcuts Taken

No significant shortcuts. The acceptance test uses real `RequestService`, `HistoryManager`,
`TemplateService`, and `HistoryPanel` with HTTP mocked at the boundary — matching the
architecture plan and existing repo conventions.

## Code Quality Issues

- `tests/test_history_masking_e2e.py` accesses private widget attributes (`_list_widget`,
  `_detail_url`, `_detail_headers`, `_detail_body`) for assertions. This follows the pattern in
  `tests/test_history_panel.py` and keeps the test focused without full MainWindow automation.
  Acceptable for integration coverage; refactor only if the panel gains a public test API.
- Helper functions (`_execute_and_persist`, `_reloaded_panel`) are local to the module. No shared
  extraction was needed; duplicating small helpers is preferred over premature test utilities.

## Missing Tests

- **Closed by this task:** integration/UI-level verification that masked values remain masked
  across persistence-reload cycle under real application wiring (debt item from PYPOST-446).
- **Still open (out of scope):**
  - Explicit metric `hidden_value_masks_applied_total` behavior with empty vs non-empty
    `hidden_keys` — [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464).
  - Full MainWindow click-through automation — not required by requirements; focused component
    chain is sufficient.
  - Response-body masking in history — outside PYPOST-446 request-surface scope.

## Performance Concerns

None introduced. The test runs in under one second with a single mocked HTTP call and one
persisted history entry.

## Follow-up Tasks

None filed from PYPOST-462. Remaining debt items are already tracked in sibling tickets:

- Masking metric empty vs non-empty hidden keys:
  [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464)
- Refactor `RequestService` history-recording block:
  [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463)
- CI/local dependency provisioning for full regression:
  [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465)
