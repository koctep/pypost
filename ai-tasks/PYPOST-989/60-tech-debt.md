# PYPOST-989: Technical Debt Analysis

## Shortcuts Taken

- `write_export_file` duplicates the small JSON write helper from
  `environment_export.py` — intentional to avoid collection → environment module
  dependency (see follow-up to extract shared helper).
- Tree selection uses `currentIndex()` only; no explicit "export this" context-menu
  action (button matches Import precedent).

## Missing Tests

- **`QTest.mouseClick` on `COLLECTION_EXPORT_BUTTON`** — method-level coverage exists via
  `button.click()` in UI tests.
- **Full UI round-trip** export → import through presenter with real parser on both sides
  (pure export → import round-trip test covers format fidelity).

## Follow-up Tasks

1. **Extract shared JSON export write helper** (`write_export_file` for dict/list
   payloads) if a third caller appears — same as PYPOST-988 debt item.
   - Priority: Low
   - **Jira:** [PYPOST-1011](https://pypost.atlassian.net/browse/PYPOST-1011)
2. **Export-all-collections to a JSON list** — import already accepts list shape; optional
   product follow-up if users need bulk backup in one file.
   - Priority: Low
   - **Jira:** [PYPOST-1012](https://pypost.atlassian.net/browse/PYPOST-1012)
3. **Context-menu Export collection** on collection rows for discoverability when the
   action row is off-screen on small windows.
   - Priority: Low
   - **Jira:** [PYPOST-1013](https://pypost.atlassian.net/browse/PYPOST-1013)

## Verdict

**SAFE TO CLOSE** — DoD met; no blockers.

## Worklog

tokens_used: 3000
role: blocker_review
step: 7
step_name: Review
