# PYPOST-317: Architecture

## Research

- `RequestSaveOrchestrator.save_as_request` opens `SaveRequestDialog`, resolves target
  collection (existing or newly created), copies `RequestData` with a new UUID and dialog name,
  persists via `RequestManager.save_request`, and expands the target collection in state.
- Existing coverage: one happy-path orchestrator test (`test_save_as_assigns_new_request_id`);
  presenter tests cover signals and tab rebinding (PYPOST-321).
- Gap: cancel paths, new-collection path, collection expansion, and manager-level source
  immutability at the orchestrator seam.

## Implementation Plan

1. Add `_mock_save_dialog` helper in `tests/test_request_save_orchestrator.py`.
2. Extend `TestRequestSaveOrchestrator` with:
   - dialog dismissed → `SaveAction.CANCELLED`
   - missing target collection → cancelled, no save
   - `new_collection_name` → `create_collection` path
   - `_ensure_collection_expanded` → state manager updated
   - source lookup unchanged after save-as with modified input copy
3. Strengthen happy-path assertions (name, `collection_id` on `SaveResult`).
4. Update `doc/dev/request_actions.md` testing table and run command.

## Components

| Component | Role |
| --------- | ---- |
| `RequestSaveOrchestrator` | Unit under test |
| `FakeRequestManager` / `FakeStateManager` | Reused fakes from `test_tabs_presenter.py` |
| `SaveRequestDialog` (mocked) | Dialog acceptance, collection, and name |

## Q&A

| Question | Answer |
| -------- | ------ |
| Production changes? | None expected; tests document existing behavior. |
| Presenter tests? | Kept as-is; orchestrator tests avoid duplicating signal/tab assertions. |
