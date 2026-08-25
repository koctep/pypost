# PYPOST-1156: Technical Debt Analysis

## Scope Note

PYPOST-1156 is a research and decomposition story with no production code — Steps 3, 4, and 5
each confirmed that fact. This step records **pre-existing product/code debt discovered during the
tab-creation audit** and routes it to the child implementation stories created in Step 2. It also
notes residual ambiguity in this task's own deliverables (if any).

## Shortcuts Taken

1. **v1 protocol choice is creation-time only.** FR-1.3 and the architecture decision register
   defer post-creation protocol switching on blank tabs to a future release. Users who pick the
   wrong protocol must close the tab and open a new one. This is an intentional v1 scope cut, not
   an oversight — but it is a known UX limitation until a future story addresses it.
2. **Unified tab open API deferred.** `open_blank_tab(protocol)` plus existing
   `open_websocket_tab(connection)` covers v1; full unification of Collections-open and
   blank-open paths is explicitly deferred (`20-architecture.md` Q&A).
3. **No Step-3 red tests named in PYPOST-1156.** Red tests are delegated to each child story's
   own Step 3 per the pattern in `20-architecture.md` — same precedent as PYPOST-1124.

## Code Quality Issues

Pre-existing issues in the codebase (not introduced by PYPOST-1156):

| Issue | Location | Impact |
| --- | --- | --- |
| **`tabs_presenter.py` module size** | `pypost/ui/presenters/tabs_presenter.py` | Already at PYPOST-1123 size caps; blank-tab routing and picker must be extracted to new modules (WS-TM-1/2) rather than further inflating this file |
| **HTTP-only blank-tab factory** | `TabsPresenter.add_new_tab()` → `_create_request_tab()` | No protocol-aware entry API; all blank tabs are HTTP `RequestTab` |
| **`_current_tab()` returns `RequestTab \| None` only** | `tabs_presenter.py` | Global shortcuts in `main_window.py` silently no-op on WebSocket tabs |
| **Collections context menu incomplete for WebSocket** | `collection_tree_actions._resolve_item_target()` | Rename, Delete, and New tab broken or missing for `WebSocketConnection` items despite core strategies existing for `item_type == "websocket"` |
| **WebSocket save signal not wired** | `main_window_signals.py` | `WebSocketPresenter.connection_saved` emitted but not connected — draft persistence incomplete vs HTTP `RequestSaveOrchestrator` |
| **WebSocket hotkeys documented but not registered** | `pypost/ui/hotkeys.py` `SECTION_ORDER` | Help → Hotkeys omits WebSocket Session section; `doc/user/hotkeys.md` documents shortcuts that do not dispatch |

## Missing Tests

Not applicable directly (no code produced by PYPOST-1156). The Step 3 delegation pattern assigns
red tests to child stories — see `20-architecture.md` "Mandatory — Failing Repro" table. No gap
was found beyond what each child story already owns in its proposed test names.

## Performance Concerns

None identified for the research deliverables. Draft WebSocket tabs will consume
`ws_max_concurrent_sessions` slots like saved profiles once WS-TM-2 lands; no additional
performance risk beyond existing WS-4 session governance.

## Follow-up Tasks

Pre-existing debt discovered during research, mapped to Jira child stories under Epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155):

| Debt area | Description | Owner |
| --- | --- | --- |
| Blank-tab protocol selection | `Ctrl+N` / **+** always create HTTP; no picker | [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) (WS-TM-1) |
| Metrics protocol label | `track_gui_new_tab_action` lacks `protocol` dimension | [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) (WS-TM-1) |
| `tabs_presenter.py` extraction | Picker + blank-tab factories in dedicated modules | [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157), [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) (WS-TM-1, WS-TM-2) |
| Blank WebSocket draft tab | No `add_blank_websocket_tab()`; drafts excluded from session restore | [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) (WS-TM-2) |
| Close-last-tab HTTP fallback | Empty workspace opens HTTP tab without protocol choice | [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159) (WS-TM-3) |
| **Collections menu parity** | New tab / rename / delete broken for WebSocket items | [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160) (WS-TM-4) |
| **Save wiring** | `connection_saved` not connected; no `WebSocketSaveOrchestrator` | [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161) (WS-TM-5) |
| **Hotkeys** | WebSocket Session shortcuts not registered or dispatched | [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162) (WS-TM-6) |
| User doc / dev doc alignment | `doc/user/*` and dev docs describe controls that do not exist | [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163) (WS-TM-7) |

### New debt surfaced by this research (documentation)

1. **`doc/dev/websocket_ui_client.md` claims full Collections rename/delete support** (Overview,
   line 16) but the audit found rename/delete menu resolution broken for WebSocket items.
   Addressed in Step 8 by adding a "Planned" section; full correction ships with WS-TM-4 and
   WS-TM-7.
2. **`doc/user/websocket.md` step 1 references a non-existent mode selector** — critical doc/code
   gap; tracked to WS-TM-7 after implementation stories land.

**Pre-existing test failures:** none apply — no test suite was run during this research task.

None of the follow-ups above block Step 8 (Dev Docs) or COMMIT for PYPOST-1156 itself. They are
the intended output of the decomposition: pre-existing debt routed to named implementation
stories rather than fixed in the research task.
