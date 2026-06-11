# PYPOST-321: Architecture

## Research

- `TabsPresenter._handle_save_as_request` copies `RequestData` with `model_copy(deep=True,
  update={"id": str(uuid.uuid4()), ...})` before calling `RequestManager.save_request`.
- Existing test `test_save_as_emits_request_save_as_completed_not_request_saved` checks the
  completion signal carries a new ID and does not emit `request_saved`.
- Gap: no assertion that the source ID remains registered in the manager and that `save_request`
  is never invoked with the source ID.

## Implementation Plan

1. Add `test_save_as_preserves_original_request_id` to `tests/test_tabs_presenter.py`.
2. Arrange a persisted source request (`r1`) in `FakeRequestManager`.
3. Drive `_handle_save_as_request` with a mocked `SaveRequestDialog`.
4. Assert:
   - `find_request("r1")` still returns the original entity unchanged.
   - `save_request` received exactly one call with `id != "r1"`.
   - Input `request_data.id` remains `"r1"` after the flow (source not mutated in place).
   - Active tab is rebound to the new request ID.

## Components

| Component | Role |
| --------- | ---- |
| `TabsPresenter` | Save-as orchestration under test |
| `FakeRequestManager` | Records `save_request` calls and simulates lookup |
| `SaveRequestDialog` (mocked) | Supplies target collection and new name |

## Q&A

| Question | Answer |
| -------- | ------ |
| Why presenter-level test? | Save-as ID assignment happens in `TabsPresenter`; unit test is fast and precise. |
| Production code changes? | None expected; test documents and guards existing behavior. |
