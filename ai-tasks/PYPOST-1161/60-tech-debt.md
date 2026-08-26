# PYPOST-1161: Technical Debt Analysis

## Shortcuts Taken

- **Reused HTTP save dialog copy.** `SaveRequestDialog` still shows HTTP-oriented labels ("Save Request", "Request Name:") for WebSocket first-save and Save As flows. Functionally correct; UX copy deferred.
- **Sibling stale-tab prompts not wired for WebSocket.** `TabsPresenter.websocket_persisted` is emitted on overwrite save but has no slot equivalent to HTTP `request_persisted` → `_offer_stale_tab_resolution`. Stale overwrite on the *saving* tab is handled via `StaleCheckContext`; other open tabs sharing the same profile id are not prompted yet.
- **Handlers kept inline in `tabs_presenter.py`.** Architecture suggested `tabs_presenter_ws_save.py` if LOC cap bites; file size did not force extraction in this story.

## Code Quality Issues

- `WebSocketTab` uses `save_requested` / `save_as_requested` signal names (HTTP `RequestWidget` parity) rather than the architecture doc's `profile_save_*` names — intentional to match existing presenter wiring; architecture doc naming is stale.
- `websocket_persisted` signal is defined and emitted but unused by any connected handler — dead emission until sibling stale flow is implemented.
- First-save path on `_handle_save_websocket` does not emit `websocket_persisted` (only overwrite does); HTTP emits `request_persisted` on overwrite only as well — consistent, but sibling WS tabs won't refresh from disk on another tab's first save until refresh_tree runs.

## Missing Tests

- No automated test for **overwrite save** with `confirm_overwrite_request` enabled end-to-end through `WebSocketTab` (orchestrator unit test covers orchestrator; integration tests cover draft first-save only).
- No test for **sibling tab stale prompt** after WebSocket overwrite (feature not implemented — see Follow-up Tasks).
- No test asserting **SaveRequestDialog** shows WebSocket-specific labels (labels not parameterized yet).

All PYPOST-1161 tests declare explicit timeout markers (`pytestmark` on each test module/class).

## Performance Concerns

None identified at current scale. Save As uses incremental `add_saved_websocket_to_tree`; Save / overwrite uses full `refresh_tree` via `websocket_saved` (same as HTTP Save path — acceptable per `collection_tree_performance.md`).

## Follow-up Tasks

1. **Wire `websocket_persisted` to sibling stale-tab resolution** — mirror HTTP `_on_request_persisted` / `_offer_stale_tab_resolution` for `WebSocketTab` (reload or set `stale_persisted` on sibling tabs sharing `ws_id`).
2. **Parameterize `SaveRequestDialog` labels** for WebSocket profile save (or add thin wrapper) so dialog copy matches requirements UX.
3. **Add integration test for WebSocket overwrite save** from Actions menu on a collection-backed tab (confirm + tree refresh).
4. **Extract WS save handlers to `tabs_presenter_ws_save.py`** if `tabs_presenter.py` grows past maintainability threshold in a future tab-management story.
5. **Update architecture artifact signal names** in `20-architecture.md` to match shipped `save_requested` / `save_as_requested` on `WebSocketTab`.
