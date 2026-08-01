# PYPOST-941 Requirements

Share tree DisplayRole text walk between `ui_select` and `agent_e2e_tree`.

Parent: [PYPOST-916](../PYPOST-916/60-tech-debt.md) TD-3.

## User Stories

- As a **maintainer**, I want one depth-first DisplayRole tree walk so
  `ui_select` and e2e click helpers cannot drift.
- As a **test author**, I want `find_tree_index_by_text` to find nested rows
  beyond two levels, matching agent select semantics.

## Acceptance Criteria

- [x] One shared walk function used by `pypost/agent/ui_actions.py` and
  `tests/helpers/agent_e2e_tree.py`.
- [x] `agent_e2e_tree.find_tree_index_by_text` raises `AssertionError` on
  miss; `ui_select` continues to raise `UiTargetNotInteractableError`.
- [x] Existing `tests/test_ui_actions.py` and agent e2e tests remain green.
- [x] New test proves deep (3+ level) tree lookup via e2e helper.

## Out of Scope

- Replacing viewport click with `ui_select` for open-request flows.
- Sharing flat list DisplayRole scan (separate debt).
