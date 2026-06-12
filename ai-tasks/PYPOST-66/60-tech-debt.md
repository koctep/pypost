# PYPOST-66: Technical Debt Analysis

## Summary

**SAFE TO CLOSE.** Signal wiring extraction complete; behavior unchanged; caps satisfied.

## Resolved

| Item | Status |
|------|--------|
| TD-1 (partial) — inline presenter wiring in `main_window.py` | **Improved** — wiring in `main_window_signals.py` |

## Remaining (non-blocker)

| Item | Priority | Follow-up |
|------|----------|-----------|
| `main_window.py` still 260 LOC vs PYPOST-43 ≤ 150 target | LOW | Future PYPOST-43 chunks: layout, menus/shortcuts, settings flow |
| `MainWindow` class 222 LOC | LOW | Same — incremental extraction |

## Follow-ups

None requiring new Jira issues for this ticket. Remaining TD-1 work stays under PYPOST-43 /
existing backlog.
