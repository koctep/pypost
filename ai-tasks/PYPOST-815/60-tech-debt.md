# PYPOST-815: Technical Debt

## Shortcuts Taken

- Baseline-only approach: 177 UI errors frozen without fixes (same pattern as PYPOST-734 for core).
- `types-PySide6` stubs reduce but do not eliminate Qt typing gaps (`attr-defined` dominates).

## Residual Debt

| Item | Severity | Notes |
| --- | --- | --- |
| 177 UI baseline mypy errors (29 files) | Medium | Top: `mixins.py` (36), `collection_item_dialogs.py` (26) |
| 41 core baseline errors | Medium | Parent triage in PYPOST-734; unchanged by this task |
| PySide6 stub version lag | Low | `types-PySide6` 6.10.x vs runtime `PySide6==6.11.1` |

## Blocker Review

**SAFE TO CLOSE** — UI scope added to mypy baseline gate; PySide6 stubs configured; postponed
annotations complete; `make check` and `make typecheck` pass.

## Follow-up Tasks

Remaining baseline work is ticketed under parent [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734):

| Item | Jira |
| --- | --- |
| R-P2-005 — Core baseline triage (41 errors) | [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734) |
| UI attr-defined guards in `mixins.py` | Future debt item when touching hover code |
| Dialog helper typing in `collection_item_dialogs.py` | Future debt item when touching dialogs |

No new Jira follow-ups introduced by this task.
