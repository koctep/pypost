# PYPOST-798: Technical Debt Analysis

## Shortcuts Taken

None. Straightforward regression tests with no production changes.

## Code Quality Issues

None introduced.

## Missing Tests (resolved)

| Scenario | Status |
| --- | --- |
| **`tabBarClicked` fallback emits `new_tab_requested`** | Covered (`test_plus_tab_tab_bar_clicked_emits_new_tab_requested`) |
| **Fallback adds request tab via presenter** | Covered (`test_plus_tab_tab_bar_clicked_adds_request_tab`) |
| **Non-plus index does not emit** | Covered (`test_non_plus_tab_bar_clicked_does_not_emit_new_tab`) |
| Primary `+` button click | Already covered (PYPOST-797) |
| macOS native chrome click geometry | Not automatable — synthetic emit is acceptable per architecture |
| End-to-end `MainWindow` + chrome click | Out of scope — header/presenter unit tests sufficient |

## Performance Concerns

None.

## Follow-up Tasks

No new follow-ups. This task closes the PYPOST-797 debt item for fallback test coverage.

## Blocker Review

**Verdict: SAFE TO CLOSE**

No blockers. All acceptance criteria met.
