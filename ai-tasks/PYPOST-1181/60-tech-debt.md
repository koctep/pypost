# PYPOST-1181: Technical Debt Analysis

Test-only isolation for the WebSocket UI connect/disconnect lifecycle
(`tests/test_websocket_client_ui_repro.py`). No production `pypost/` changes.
There is **no AC-breaking debt** in this fix. Remaining items are naming /
duplication cleanup, intentional hermetic shortcuts, and pre-existing suite
failures already ticketed elsewhere. None block Step 8.

## Shortcuts Taken

1. **File-local `_SilentMockTransport` instead of a shared helper.** Architecture
   allowed an inline double; engine/controller suites already define their own
   `MockTransport` / `DummyTransport`. Duplication is small and scoped to this
   UI repro module. Extracting `tests/helpers/` was deferred to avoid drive-by
   suite churn.

2. **Step 3 deferred-fail harness converted to a silent-mock green check.**
   Architecture required dropping or narrowing the permanently red
   `DeferredFailTransport` harness once isolation landed. The former red node
   `test_presenter_lifecycle_open_overwritten_by_deferred_transport_failure`
   now uses `_SilentMockTransport` and asserts Open survives a bounded
   `processEvents` pump. The race class is documented in the docstring and in
   `20-architecture.md`, not by a live deferred-fail test in CI.

3. **Hermetic `_http_protocol_picker` on all `TabsPresenter` constructions in
   this file.** Closing the last WebSocket tab was hanging on the modal
   `NewTabProtocolPicker` (pre-existing at base `2f33a393`). Injection returns
   `TabProtocol.HTTP` without `QMenu.exec()`, matching the PYPOST-1157
   testability pattern. CI still does not exercise the live picker popup on
   this close-last-tab path (owned by PYPOST-1159 / PYPOST-1180).

4. **Disconnect still driven by synthetic `state_changed.emit(IDLE)`.** Open
   uses `controller.on_opened("")` (listener path). Close/Idle remains a
   direct signal emit, consistent with older UI repro style. Sufficient for
   button/enablement asserts; does not exercise transport `on_closed` →
   controller teardown.

5. **`set_listener` discards the listener.** Silent mock never emits callbacks;
   Open is driven through the controller listener API instead. Intentional —
   the double must not auto-fail or auto-open.

## Code Quality Issues

| Issue | Location | Notes |
| ----- | -------- | ----- |
| Misleading test name | `test_presenter_lifecycle_open_overwritten_by_deferred_transport_failure` | Name still says “deferred…failure” but the body is hermetic silent-mock survival of Open. Rename (or merge into the primary lifecycle test) in a small follow-up. |
| Near-duplicate lifecycle coverage | Same node vs `test_presenter_connect_and_disconnect_lifecycle` | Both inject `_SilentMockTransport`, call `handle_connect`, drive Open, pump events, assert Disconnect. The second adds a 0.5s bounded pump loop and `opened_target` assert. Prefer one regression guard + optional short pump on the primary test. |
| Repeated MockTransport shapes | UI repro vs `test_websocket_session_engine_repro.py` / controller DummyTransport | Acceptable per architecture; extract only if a third copy appears. |
| Disconnect not listener-driven | `test_presenter_connect_and_disconnect_lifecycle` | Synthetic Idle emit; low risk for label asserts. |

Hardcoded `echo.example.com` sample URLs and `_http_protocol_picker` → HTTP are
intentional hermetic fixtures, not magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Module declares
`pytestmark = pytest.mark.timeout(30)`. All 19 tests in
`tests/test_websocket_client_ui_repro.py` inherit it.

In-scope AC coverage is present:

- Connect → Connecting (Cancel / editor locked) → Open (Disconnect / send
  enabled) → Disconnect → Idle under hermetic transport
- Extra `processEvents` after Open does not revert to Connect
- Close-last-tab / TabsPresenter paths no longer block on modal picker

Gaps that remain (none are AC breaks for this debt item):

- **No CI test that still injects `DeferredFailTransport`.** Intentional —
  architecture forbade leaving a permanently red race harness. Product
  FAILED→Connect behavior stays covered by session/engine tests with real or
  controllable failures.
- **No disconnect via `on_closed` / transport close.** Synthetic Idle is enough
  for UI labels; full close handshake belongs to session-engine coverage.
- **Live `NewTabProtocolPicker.prompt` / `exec()` still untested** (pre-existing
  PYPOST-1157 shortcut; [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180)).

## Performance Concerns

None material for production (no production code changed).

Suite-side notes:

1. **Hermetic transport removes** live DNS/TLS/socket and reconnect-timer work
   that caused intermittent HostNotFound races and mid-suite hangs — net win.
2. **0.5s pump loop** in
   `test_presenter_lifecycle_open_overwritten_by_deferred_transport_failure`
   adds ~0.5s wall time per module run. Bounded and intentional; removable if
   the test is merged into the primary lifecycle check with a shorter extra
   `processEvents` pump (already present there).

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues for unticketed items. Step 7
does not. Pre-existing suite failures already have keys from PYPOST-1192 triage.

### Implementation follow-ups (this task’s leftovers)

1. **NON-BLOCKER — rename or merge redundant green regression test**
   - Rename
     `test_presenter_lifecycle_open_overwritten_by_deferred_transport_failure`
     to reflect silent-mock Open survival, **or** fold the `opened_target` +
     short pump asserts into
     `test_presenter_connect_and_disconnect_lifecycle` and delete the
     duplicate.
   - Priority: Low (clarity / suite time only).
   - Jira: [PYPOST-1200](https://pypost.atlassian.net/browse/PYPOST-1200)

2. **NON-BLOCKER — optional shared silent MockTransport helper**
   - Extract only if another UI module needs the same double; otherwise leave
     file-local.
   - Priority: Low.
   - Jira: [PYPOST-1201](https://pypost.atlassian.net/browse/PYPOST-1201); can ride a broader WS test-helpers cleanup.

3. **NON-BLOCKER — docs for hermetic UI lifecycle testing** — **done in Step 8**
   - Documented in `doc/dev/websocket_ui_client.md` (primary), plus
     `websocket_session_engine.md`, `gui_testing.md`,
     `new_tab_protocol_picker.md`, and `last_tab_protocol_picker.md`:
     UI lifecycle tests must inject `set_transport_factory` (and hermetic
     `protocol_picker` when constructing `TabsPresenter`) so Connect never
     opens live sockets / modal pickers.
   - Priority: Low; owned by this task’s Step 8.

### Pre-existing / filed suite issues (NON-BLOCKER)

Reconfirmed during Step 5 `make check` (same four files as PYPOST-1192 triage
at base `2f33a393` / `18a4d9d1`). Not caused by this test-isolation change;
in-scope module is green (19 passed).

| Item | Verdict | Jira |
| ---- | ------- | ---- |
| Collection item delete/rename `_unpack_context` arity | NON-BLOCKER — pre-existing | [PYPOST-1193](https://pypost.atlassian.net/browse/PYPOST-1193) |
| Node ids: `tests/test_collection_item_strategies.py::CollectionItemStrategiesTests::test_builtin_strategies_delegate_to_request_manager_methods`; `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_delete_collection_item_routes_by_type`; `…::test_delete_collection_item_routes_collection_type`; `…::test_rename_collection_item_rejects_empty_name`; `…::test_rename_collection_item_routes_collection_type` | | |
| SOLID `FILE_CAPS` drift (`test_audit_module_inventory_within_caps`) | NON-BLOCKER — pre-existing | [PYPOST-1194](https://pypost.atlassian.net/browse/PYPOST-1194) |
| Node id: `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps` | | |
| WebsocketDraftObservability caplog assertions | NON-BLOCKER — pre-existing | [PYPOST-1195](https://pypost.atlassian.net/browse/PYPOST-1195) |
| Node ids: `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_save_tabs_state_logs_omitted_websocket_draft_id`; `…::test_save_tabs_state_logs_persisted_saved_websocket_id` | | |

Related out-of-scope (not re-failed in this task’s check, already ticketed):

- MCP port-busy flake: [PYPOST-1196](https://pypost.atlassian.net/browse/PYPOST-1196) /
  [PYPOST-1178](https://pypost.atlassian.net/browse/PYPOST-1178)
- Collections import hang: [PYPOST-1182](https://pypost.atlassian.net/browse/PYPOST-1182)

**Resolved by this task (no further follow-up):** the original
`test_presenter_connect_and_disconnect_lifecycle` HostNotFound / Connect-after-
Open flake and the modal-picker hang of `test_websocket_client_ui_repro.py`
that were filed as PYPOST-1181 from PYPOST-1157 / PYPOST-1192.
