# PYPOST-988: Technical Debt Analysis

## Shortcuts Taken

- Export reuses `serialize_environment` without a separate export-only format — intentional
  for import round-trip.
- `build_export_payload` duplicates single-vs-list shaping also done in the widget; kept
  in core for testability while widget inlines the same rule via `serialize_export_records`
  + `write_export_file`.

## Missing Tests

- **`EnvPresenter`-level test** for `serialize_export_records` lambda (same gap as
  PYPOST-986 import wiring).
- **`QTest.mouseClick` on `ENV_EXPORT_BUTTON`** — method-level coverage exists.
- **Encrypted-at-rest export → import on same machine** through full UI path (pure round-
  trip test covers logic with encryption off).

## Follow-up Tasks

1. **Add `EnvPresenter` export wiring test** using `FakeStorageManager` — confirm
   `serialize_export_records` reaches `EnvironmentDialog`.
   - Priority: Low
   - **Jira:** [PYPOST-1008](https://pypost.atlassian.net/browse/PYPOST-1008)
2. **Add encrypted export round-trip integration test** with `PYPOST_ENV_ENCRYPTION_ENABLED`
   and a temp key — verify envelope shape in file and successful re-import.
   - Priority: Low
   - **Jira:** [PYPOST-1009](https://pypost.atlassian.net/browse/PYPOST-1009)
3. **Extract shared single-vs-list JSON root helper** if a third import/export caller
   appears — avoid duplicating the rule in widget and `build_export_payload`.
   - Priority: Low
   - **Jira:** [PYPOST-1010](https://pypost.atlassian.net/browse/PYPOST-1010)

## Verdict

**SAFE TO CLOSE** — DoD met; no blockers.

## Worklog

tokens_used: 4000
role: blocker_review
step: 7
step_name: Review
