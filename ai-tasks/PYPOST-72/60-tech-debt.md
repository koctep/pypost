# PYPOST-72 — Tech Debt Review

## Verdict: SAFE TO CLOSE

## Resolved Items

| ID | Item | Status |
|----|------|--------|
| TD-8 (PYPOST-43) | `currentIndex()` read after save dialog exec | Resolved |

## Follow-Ups

| ID | Item | Priority | Jira |
|----|------|----------|------|
| TD-save-wire | Pass explicit tab ref at save/save-as signal wire time (like send) | LOW | Deferred — reduces reliance on `_find_tab_for_sender` |

Note: `_find_tab_for_sender` remains for save/copy paths; wire-time closure is future work.
