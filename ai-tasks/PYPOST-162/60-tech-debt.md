# PYPOST-162 — Tech Debt Review

## Verdict: SAFE TO CLOSE

## Resolved Items

| ID | Item | Status |
|----|------|--------|
| Manual Signal Connection (PYPOST-22) | Save/save-as used `_find_tab_for_sender` / scattered wiring in `add_new_tab` | Resolved |
| TD-save-wire (PYPOST-72) | Pass explicit tab ref at save signal wire time | Resolved |
| TD-save-sender (PYPOST-71) | Save handlers relied on `self.sender()` | Resolved |

## Follow-Ups

None — copy-curl does not need tab binding today.
