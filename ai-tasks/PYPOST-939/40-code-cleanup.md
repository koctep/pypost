# PYPOST-939: Code Cleanup

## Changes Reviewed

- `_select_item_view` in `pypost/agent/ui_actions.py` — flat model scan;
  no duplication with `_select_list` (widget API stays separate).
- Test helpers `_make_list_view_fixture` / `_close_list_view_fixture` mirror
  existing tree fixture teardown (`setModel(None)`).
- Docstring updates on `ui_select` and `AgentAppSession.ui_select`.

## Cleanup Actions

- No dead code introduced.
- Dispatch order documented in architecture (subclass before base).
- Error messages consistent with list/tree helpers (`option not found`,
  `option index out of range`, `item view has no model`).

## Deferred (non-blocker)

- Shared flat DisplayRole scan could merge with tree walk later if more
  model views appear (see `60-tech-debt.md`).
