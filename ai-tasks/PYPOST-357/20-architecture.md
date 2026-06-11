# PYPOST-357: Architecture — Response Search Flow Integration Tests

## Research

- `RequestTab` embeds `ResponseView` and receives bodies via `display_response` after requests
  finish (`TabsPresenter._on_request_finished`).
- `ResponseView` wires `search_input.textChanged` → `_schedule_search_text_changed`, Next button
  → `_find_next`, and `returnPressed` → `_find_next(source="enter")`.
- `tests/test_response_view_search.py` calls `_on_search_text_changed` and `_find_next` directly.
- `tests/test_save_flow_integration.py` and `tests/test_new_variable_flow_integration.py`
  establish the integration-test pattern for presenter wiring.

## Implementation Plan

1. Add `tests/test_response_search_flow_integration.py` with `TestResponseSearchFlowIntegration`.
2. Reuse `FakeRequestManager`, `FakeStateManager`, and `_active_tab` helpers from sibling tests.
3. Populate body via `display_response` on the active tab's `ResponseView`.
4. Drive search via `QTest.keyClicks`, `setText` (textChanged path), Next button, and Enter.
5. Assert match counter label after each step.

## Test Matrix

| Test | Entry point | Expected outcome |
| ---- | ----------- | ---------------- |
| `test_type_and_next_button_updates_match_counter` | keyClicks + Next | `1 of 3` → `2 of 3` → `3 of 3` |
| `test_enter_key_finds_next_match` | setText + Return | `1 of 3` → `2 of 3` |
| `test_typed_query_with_no_matches` | setText | `No matches` |
| `test_new_response_clears_search_via_display_response` | display_response | empty input and label |

## Q&A

| Question | Answer |
| -------- | ------ |
| Production code changes? | None expected; tests document and guard existing wiring. |
| Why mix keyClicks and setText? | keyClicks exercises typing on small bodies; setText covers textChanged for Enter test. |
