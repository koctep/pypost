# PYPOST-1159: Technical Debt Analysis

PYPOST-1159 (WS-TM-3) shipped last-tab empty-workspace replacement through
`handle_new_tab("last_tab")` after extracting `close_workspace_tab` to
`tabs_presenter_close.py`. In-scope AC is met: picker before replacement,
HTTP / WebSocket / MCP outcomes via `open_blank_tab`, cancel leaves an
empty strip, dirty WS discard-or-keep still runs first, restore unchanged,
and `gui_new_tab_actions_total{source="last_tab"}` is registered.

There is **no AC-breaking debt** in this story's own change. Remaining
items are intentional epic deferrals, the still-open presenter LOC extract
([PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)), a few
narrow test gaps, and dev-doc drift that Step 8 must fix.

Phase D of the orchestrator creates Jira issues. This step does not.
New follow-ups omit browse links. Existing keys are cited for context
only.

Out of scope for this file (not caused here, not listed as 1159 debt):
unrelated working-tree files (`mcp_server.py`, `port_allocation.py`);
baseline mypy reds outside the tabs presenter stack.

## Shortcuts Taken

1. **Close-tab extract only — insert-before-plus extract deferred.**
   Step 4 moved `close_tab` orchestration to
   `tabs_presenter_close.py` so `tabs_presenter.py` dropped to **770 /
   785** LOC (15 lines headroom). The triplicated insert-before-plus
   sequence in `add_new_tab`, `_insert_websocket_tab`, and
   `add_blank_mcp_client_tab` was **not** consolidated. That work remains
   [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184) (To Do).
   This story does **not** close 1184.

2. **`close_tabs_for_request_ids` empty strip still silent HTTP.**
   Collections bulk delete that removes every workspace tab still calls
   `add_new_tab(save_state=False)` when `_request_tab_count() == 0`
   (`tabs_presenter.py`). Architecture marked this out of scope (not a
   user last-tab close). Parity with last-tab picker is a product gap for
   a future story if bulk-delete empty workspace should also ask protocol.

3. **`prompt_close` passed from `TabsPresenter.close_tab` into
   `close_workspace_tab`.** Mirrors PYPOST-1158: tests patch
   `tabs_presenter.prompt_unsaved_draft_tab_close`. Production always
   passes the real callable; the helper default is unused on that path.

4. **`TestTabsPresenter._make_presenter` injects HTTP picker globally.**
   `protocol_picker=lambda: TabProtocol.HTTP` keeps legacy tests (e.g.
   `test_close_tab_ensures_at_least_one_tab`) green without exercising
   cancel-on-last-close. Last-tab behavior is isolated in
   `TestCloseLastTabProtocolPicker`, which injects its own picker.

5. **User-facing docs not rewritten here.** Last-tab parity in `doc/user/`
   is [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163).
   `doc/dev/` updates are Step 8 of this task (several pages still describe
   pre-1159 close-last-tab behavior).

## Code Quality Issues

Implementation matches the chosen architecture: single blank-tab entry
via `handle_new_tab("last_tab")`, extracted close helper, metrics source
registered, restore untouched.

- **Presenter LOC — `tabs_presenter.py` 770 / 785.**
  Headroom exists after the close extract, but **PYPOST-1184** (shared
  insert-before-plus helper) is still To Do. Ticket text may still cite
  older LOC from PYPOST-1166 / 1158. Future stories that grow factories
  or restore should land 1184 before adding lines.

- **Triplicated insert-before-plus** in `add_new_tab`,
  `_insert_websocket_tab`, and `add_blank_mcp_client_tab` — same
  `insert_index_before_plus` / `setCurrentWidget` / optional
  `save_tabs_state` block. Extract when PYPOST-1184 runs.

- **`close_workspace_tab` uses `TYPE_CHECKING` presenter import.**
  Correct for avoiding cycles; mirrors `tabs_presenter_draft.py`. Not a
  defect.

- **`websocket_id_is_saved` per lookup** (from PYPOST-1158) — unchanged
  by this story; still rebuilds `WebSocketRegistry` per call inside
  `confirm_close_websocket_draft`. Wasteful at scale; bind one registry
  when someone next touches draft close helpers.

No architecture deviation that requires a 1159 fix. Planned rejections
(restore picker, raising the 785 cap, closing 1184 without insert-before-
plus) were followed.

## Missing Tests

**Timeout markers: no BLOCKER.** Scoped modules declare explicit timeouts:

- `tests/test_tabs_presenter.py` — `pytestmark = pytest.mark.timeout(60)`
  (covers `TestCloseLastTabProtocolPicker`)
- `tests/test_metrics_manager.py` — module `pytestmark` includes timeout

In-scope AC coverage is present for last-tab picker path (7 tests in
`TestCloseLastTabProtocolPicker`), metrics source
(`test_track_gui_new_tab_action_last_tab_source`), dirty WS keep/discard
ordering, non-last close skip, HTTP / WS confirm, and cancel-without-tab.

Gaps (non-blocking):

| Gap | Risk | Notes |
| --- | --- | --- |
| No `test_restore_mixed_saved_http_and_websocket_workspace` | Low | Step 2 planned an explicit mixed-workspace **lock**; not added. Separate restore tests exist; mixed HTTP+WS together is implicit, not locked. |
| No last-tab **MCP Client** confirm test | Low | Picker menu includes MCP; `handle_new_tab` MCP path tested for `shortcut` / `plus_button`, not `last_tab`. Same `open_blank_tab` code; attribution only. |
| No dedicated `source=last_tab` **INFO** log tests | Low | Observability reuses `handle_new_tab` events; cancel/confirm log tests exist for other sources. |
| `test_close_tab_ensures_at_least_one_tab` name vs behavior | Low | Still asserts count stays 1 via injected HTTP picker, not "user cannot empty workspace." Cancel path covered in `TestCloseLastTabProtocolPicker`. |
| `close_tabs_for_request_ids` empty fallback | Low | Out of scope; no picker parity test or change. |

HTTP dirty-close on last tab (blank HTTP draft with edits) remains
unimplemented from PYPOST-1158; unticketed unless epic picks it up.

## Performance Concerns

None introduced. Last-tab close adds one synchronous picker call on an
already user-driven path. No new network, disk, or background work.
`save_tabs_state()` after empty cancel persists empty `open_tabs` as
before.

## Follow-up Tasks

1. **BLOCKER-adjacent — presenter LOC extract (still open)**

   - Extract shared insert-before-plus helper used by HTTP / WS / MCP
     factories; shrink `tabs_presenter.py` further and remove triplication.
   - **Not closed by PYPOST-1159** — close-tab extract alone is
     insufficient.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)
     (To Do)

2. **NON-BLOCKER — dev docs drift (Step 8)**

   - Update `doc/dev/new_tab_protocol_picker.md` (close-last-tab row and
     troubleshooting still say `add_new_tab(save_state=False)`).
   - Update `doc/dev/websocket_draft_tab.md` / `mcp_client_draft_tab.md`
     cross-links where they reference pre-1159 fallback.
   - Owner: PYPOST-1159 Step 8

3. **NON-BLOCKER — mixed restore lock test**

   - Add `test_restore_mixed_saved_http_and_websocket_workspace` per Step 2
     plan: `open_tabs=[http_id, ws_id]` restores both kinds; no picker.
   - Owner: optional follow-up or ride on next restore-touching story

4. **NON-BLOCKER — last-tab MCP metric test**

   - `TestCloseLastTabProtocolPicker` case: picker returns MCP →
     `McpClientTab`, metric `source=last_tab`, `protocol=mcp_client`.
   - Owner: optional polish

5. **NON-BLOCKER — bulk-delete empty workspace parity**

   - If product wants protocol picker when `close_tabs_for_request_ids`
     empties the strip, route through `handle_new_tab` with a new source
     label (not `last_tab`). New story; out of 1159 scope.

6. **NON-BLOCKER — user docs**

   - Last-tab parity in User Guide: [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163)

7. **NON-BLOCKER — HTTP dirty-close on last tab**

   - Reuse `prompt_unsaved_draft_tab_close` for blank HTTP drafts on close;
     unticketed; inherited from PYPOST-1158 analysis.
