# PYPOST-1158: Technical Debt Analysis

PYPOST-1158 (WS-TM-2) shipped registry-gated draft omit (FR-5) and
factory-compare dirty-close (FR-8) on the existing `WebSocketTab` stack.
There is **no AC-breaking debt** in this story's own change. Remaining
items are intentional epic deferrals, presenter LOC at the audit cap,
narrow dirty-close test coverage, and a few helpers that PYPOST-1161
must replace rather than extend blindly. None of those items block
Step 8.

Phase D of the orchestrator creates Jira issues. This step does not.
New follow-ups omit browse links. Existing keys are cited for context
only.

Out of scope for this file (not caused here, not listed as 1158 debt):
unrelated working-tree files (`mcp_server.py`, PYPOST-1176,
`port_allocation.py`); baseline mypy reds in
`pypost/core/qt/websocket_stream_export_worker.py` and
`pypost/ui/dialogs/settings_dialog.py`.

## Shortcuts Taken

1. **Factory-compare dirty detection instead of `WebSocketTab.persisted_baseline`.**
   Architecture rejected a disk snapshot this story: drafts have no
   collection row until [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161).
   `is_websocket_draft_dirty` compares a mixed editor/model snapshot to
   `factory_websocket_draft()`. After first save, factory-compare is the
   wrong baseline (a saved tab that still matches factory defaults would
   look "clean"; a saved tab that differs from factory would look
   "dirty" even if it matches disk). PYPOST-1161 must adopt a persisted
   snapshot and stop using factory-compare for saved profiles. This
   story already skips the prompt when `find_websocket(id)` hits, so
   saved tabs are not prompted today.

2. **HTTP `close_tab` was not wired to the new Discard / Keep dialog.**
   FR-8 is WS-draft-only. `is_tab_dirty` remains sibling-reload after
   HTTP save (`_offer_stale_tab_resolution`), not close. Blank HTTP
   tabs keep `persisted_baseline is None`, so `is_tab_dirty` is False.
   `prompt_unsaved_draft_tab_close` now exists and can be reused later.
   Architecture cited [PYPOST-647](https://pypost.atlassian.net/browse/PYPOST-647)
   for this gap; that Debt issue is **Done** and was environment-dialog
   UX from PYPOST-54, not HTTP tab discard-on-close. HTTP close prompt
   is still unimplemented and **unticketed**.

3. **`confirm_close_websocket_draft` takes injectable `prompt_close`.**
   Architecture showed only `websocket_id_is_saved`. The extra argument
   lets `close_tab` pass `prompt_unsaved_draft_tab_close` from
   `tabs_presenter.py` so tests patch that module. Production default
   in `tabs_presenter_draft.py` is unused when the presenter passes the
   callable. Kept because tests and the 785 LOC wrap both depend on the
   presenter import.

4. **Close-last-tab / empty-workspace fallback stays HTTP-only.**
   After Discard, `close_tab` still calls `add_new_tab(save_state=False)`
   when `_request_tab_count() == 0`. Out of scope;
   [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).

5. **User-facing docs not rewritten here.** Draft omit, dirty-close, and
   empty-URL create path in `doc/user/` are
   [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163).
   `doc/dev/` is Step 8 of this task.

## Code Quality Issues

Implementation matches the chosen architecture: registry-gated
`save_tabs_state`, factory dirty-close for unsaved WS drafts only,
shared Discard / Keep dialog, helpers extracted so
`tabs_presenter.py` does not grow past the cap.

- **Presenter is at the LOC cap — `tabs_presenter.py` 785 / 785.**
  Snapshot `ai-tasks/PYPOST-376/baseline-metrics.md` still lists 779;
  this story used the remaining lines for draft imports and
  `close_tab` / `save_tabs_state` call sites. [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159)
  and [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161)
  cannot add lines without extraction. Existing Debt
  [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)
  (insert-before-plus helper) is still To Do; ticket text may still
  cite 771/785 from PYPOST-1166.

- **Split dirty snapshot in `_connection_from_websocket_tab`.**
  Handshake / MCP checkbox / description come from editor widgets;
  `name`, `mcp_params`, probe fields, `presets`, and `sequences` come
  from `tab.connection_data`. That is correct today (presets mutate
  `presenter.connection`, which is the same object as
  `tab.connection_data`). PYPOST-1161 should turn this helper into the
  single persisted snapshot rather than adding a second reader.

- **`websocket_id_is_saved` constructs a new `WebSocketRegistry` per
  lookup.** `WebSocketRegistry.__init__` always `rebuild_index()`.
  `save_tabs_state` therefore rebuilds the index once per WebSocket
  tab. Correct and cheap for GUI collections; wasteful if many WS
  tabs autosave state. Bind one registry per `save_tabs_state` /
  `close_tab` when someone next touches `tabs_presenter_draft.py`.

- **`confirm_close_websocket_draft(tab: object)`.** Architecture typed
  `WebSocketTab`. The `object` + `isinstance` gate is required because
  `close_tab` is polymorphic. Not a defect.

Hardcoded dialog copy (**Discard**, **Keep the tab**), factory dummy id
`websocket-factory-draft`, and fallback title **New WebSocket** match
FR-8 / FR-1.2. They are not magic-value debt.

No architecture deviation that requires a 1158 fix. Planned rejections
(HTTP close retrofit, `persisted_baseline` this story, omit-every-
`WebSocketTab`) were followed.

## Missing Tests

**Timeout markers: no BLOCKER.** Modules added or edited for this story
declare explicit `pytest.mark.timeout`:

- `tests/test_websocket_persisted_fields.py` — `timeout(10)`
- `tests/test_websocket_client_ui_repro.py` — `timeout(30)`
- `tests/test_tabs_presenter.py` — `timeout(60)` (module `pytestmark`
  covers `TestTabsPresenter` and `TestWebsocketDraftObservability`)
- `tests/test_collection_item_dialogs.py` — `timeout(60)`
- `tests/test_agent_e2e_websocket.py` — `timeout(60)` (plus `agent_e2e`)

In-scope AC coverage is present: omit draft id + restore creates no
`WebSocketTab`; dirty URL prompts Keep/Discard; clean draft does not
prompt; two blanks do not merge; saved-profile dedup; saved id still
persisted; dialog Discard/Keep mapping; field-equal unit tests (url,
name, MCP flag, preset); caplog for omit / persist / Keep / Discard /
clean close without URL dumps.

Gaps that remain (none are AC breaks):

- **No lock that a saved WebSocket tab skips the prompt.** Architecture:
  registry members close without Discard / Keep even if the editor URL
  changed. `test_close_dirty_websocket_draft_prompts_discard_or_keep`
  only covers drafts. A regression that prompted saved tabs would not
  be caught.

- **Dirty path is URL-only at the tab layer.**
  `is_websocket_draft_dirty` / `_connection_from_websocket_tab` have no
  direct tests. Params, headers, subprotocols, MCP description, and
  in-tab preset/sequence mutations are covered at most in
  `websocket_persisted_fields` (url / name / expose / preset list), not
  through the editor snapshot. Sequences, headers, and params have no
  model-level equal tests either.

- **No mixed draft + saved persist in one `save_tabs_state`.** Omit and
  persist are tested on separate presenters. FR-5.1 and FR-5.2 together
  (one draft omitted, one saved id kept) is untested.

- **Optional WS-4 chrome lock not added.** Architecture allowed a
  construction-only assert in `tests/test_websocket_client_ui_repro.py`;
  that file was only import-order / comment cleanup. Editor widgets
  already exist from PYPOST-1132 / PYPOST-1157.

Intentionally not missing for 1158: Save / `persisted_baseline`
(PYPOST-1161), close-last-tab picker (PYPOST-1159), live Connect e2e
(existing `test_agent_e2e_websocket.py`, patched Discard), HTTP close
prompt, user-doc tests (PYPOST-1163).

## Performance Concerns

None for draft persist or dirty-close. Registry membership and
factory-compare are synchronous GUI work on a handful of tabs. No new
I/O and no new Prometheus histograms (Step 6 N/A).

The per-lookup `WebSocketRegistry` rebuild noted above is a quality
issue, not a measured hotspot. `tabs_presenter.py` at **785 / 785** is
a capacity risk for the next stories, not a runtime cost.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. This step does not,
except citing stories that already exist.

1. **NON-BLOCKER — capacity (already ticketed; now 785 / 785)**
   - Extract shared insert-before-plus (and any other presenter fat)
     before PYPOST-1159 / PYPOST-1161 add lines.
   - Location: `pypost/ui/presenters/tabs_presenter.py` (785 / 785).
   - Why: this story consumed remaining headroom; the audit cap is
     binding.
   - Priority: High for the next presenter-touching story.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)

2. **NON-BLOCKER — intentional epic scope (not incomplete 1158 work)**
   - Save / Save As, restore-after-save, and
     `WebSocketTab.persisted_baseline`. Replace factory-compare with a
     disk snapshot for saved profiles; reuse
     `_connection_from_websocket_tab` as the snapshot helper.
   - Location: `pypost/ui/presenters/tab_dirty.py`,
     `pypost/ui/widgets/websocket/websocket_tab.py`, save orchestrator.
   - Why: factory-compare is correct only while the tab has never been
     saved.
   - Priority: High (WS-TM-5).
   - Jira: [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161)

3. **NON-BLOCKER — intentional epic scope**
   - Close-last-tab / empty-workspace picker instead of HTTP-only
     `add_new_tab` after Discard of the last navigable tab.
   - Location: `TabsPresenter.close_tab`.
   - Priority: Medium (WS-TM-3).
   - Jira: [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159)

4. **NON-BLOCKER — user docs**
   - `doc/user/` still describes WebSocket create / restore without
     draft omit and Discard / Keep close.
   - Priority: Medium (WS-TM-7).
   - Jira: [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163)

5. **NON-BLOCKER — test gap (ticket later)**
   - Lock: open a collection-backed WebSocket tab, edit the URL,
     `close_tab` must **not** call `prompt_unsaved_draft_tab_close`.
   - Add editor-snapshot dirty cases (params / headers / MCP checkbox)
     on `is_websocket_draft_dirty`; optional mixed draft+saved
     `save_tabs_state`.
   - Location: `tests/test_tabs_presenter.py`,
     `pypost/ui/presenters/tab_dirty.py`.
   - Why: FR-8 saved-skip and non-URL edits are specified but only URL
     drafts are locked.
   - Priority: Medium.
   - Jira: [PYPOST-1189](https://pypost.atlassian.net/browse/PYPOST-1189)

6. **NON-BLOCKER — HTTP draft close still has no prompt (ticket later)**
   - Wire `prompt_unsaved_draft_tab_close` for unsaved HTTP tabs once
     blank HTTP has a dirty definition (today `persisted_baseline is
     None` ⇒ `is_tab_dirty` is False). Do **not** reopen PYPOST-647
     (Done; env-dialog UX from PYPOST-54).
   - Location: `TabsPresenter.close_tab`, `tab_dirty.is_tab_dirty`,
     `collection_item_dialogs.prompt_unsaved_draft_tab_close`.
   - Why: FR-8 asked for HTTP-like Discard / Keep; HTTP itself still
     closes without that prompt. Shared dialog now exists.
   - Priority: Medium.
   - Jira: [PYPOST-1190](https://pypost.atlassian.net/browse/PYPOST-1190)

7. **NON-BLOCKER — helper quality (ticket later, or ride on PYPOST-1184)**
   - Construct one `WebSocketRegistry` per `save_tabs_state` /
     `close_tab` instead of `WebSocketRegistry(...)` inside every
     `websocket_id_is_saved` call.
   - Location: `pypost/ui/presenters/tabs_presenter_draft.py`.
   - Why: `__init__` rebuilds the full index per tab.
   - Priority: Low.
   - Jira: [PYPOST-1191](https://pypost.atlassian.net/browse/PYPOST-1191)

8. **NON-BLOCKER — Step 8 of this task (not a new ticket)**
   - Update `doc/dev/` for WS draft omit, factory dirty-close, and the
     shared Discard / Keep dialog.
   - Owned by PYPOST-1158 Step 8.
   - Jira: none
