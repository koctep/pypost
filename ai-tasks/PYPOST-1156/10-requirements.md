# PYPOST-1156: Research and decompose WebSocket tab mode UX

## Goals

Epic [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) (WebSocket tab mode —
blank-tab protocol selector) addresses a product gap left after Epic PYPOST-1123 delivered the
full WebSocket subsystem (WS-1 through WS-10, including WS-9 bounded MCP probe tools).

User-facing documentation (`doc/user/websocket.md`, step 1) instructs users to open a new tab
and select **WebSocket** mode. That control does not exist. Every blank tab created via the
primary entry points (`Ctrl+N`, tab-bar **+**) is an HTTP **Request** tab. WebSocket workspace
tabs are reachable only by opening a saved profile from **Collections** (sidebar click) or by
restoring a prior session that already held a WebSocket tab.

This mismatch blocks the documented first-run WebSocket workflow, forces users through
Collections before they can ad-hoc test a `ws://` or `wss://` endpoint, and breaks parity with
how HTTP requests are created (blank tab → compose → save). It also impedes the documented MCP
workflow (configure a profile interactively, save it, enable **Expose as MCP Tool**, preview the
agent contract) when the user has no existing WebSocket collection item.

The business goal of PYPOST-1156 is to **research, specify, and decompose** the missing
blank-tab WebSocket experience so implementation stories under PYPOST-1155 can close the
doc/code gap without rework.

## User Stories

- As a **developer testing APIs**, I want to open a blank WebSocket tab the same way I open a
  blank HTTP tab, so that I can ad-hoc connect to `ws://` or `wss://` endpoints without first
  creating a collection item.
- As a **new PyPost user**, I want the WebSocket guide's step 1 to match what I see in the app,
  so that I am not blocked on a control that does not exist.
- As a **power user**, I want `Ctrl+N` and the **+** button to let me choose (or remember) HTTP
  vs WebSocket, so that my preferred workflow is one keystroke away.
- As a **collections user**, I want right-click **New tab** on a WebSocket profile to open an
  isolated copy, mirroring HTTP requests, so that I can experiment without affecting other tabs.
- As a **collections user**, I want rename and delete in the WebSocket item context menu to
  work, so that sidebar management is consistent across item types.
- As a **developer building MCP tools**, I want to compose a WebSocket profile in a blank tab,
  save it, and enable MCP exposure, so that the WS-9 probe workflow is achievable entirely
  from the GUI.
- As a **returning user**, I want restored WebSocket tabs and newly created blank tabs to
  behave predictably, so that session restore and "always one tab open" rules do not silently
  switch me to HTTP.
- As a **keyboard-driven user**, I want WebSocket shortcuts documented in Help → Hotkeys to
  apply when a WebSocket tab is focused, so that Connect/Send/Save work as documented.

## Definition of Done (PYPOST-1156 — research task)

PYPOST-1156 is done when:

1. Tab creation flows are audited and documented (audit table incorporated in Task Description).
2. Doc/code gaps are enumerated with severity.
3. MCP alignment is assessed at product level (no runtime change required for WS-9).
4. User stories and functional requirements for blank-tab WebSocket mode are written.
5. Child implementation stories are proposed on the roadmap for Epic PYPOST-1155.
6. `ai-tasks/PYPOST-1156/10-requirements.md` and `00-roadmap.md` exist and Step 1 remains
   `[/]` pending orchestrator review.

## Task Description

### Programming Language

Python is the implementation language for the PyPost desktop client (PySide6 UI, presenters,
core services) and automated test suites. English Markdown is used for workflow and user
documentation artifacts.

### Problem

PyPost ships a complete WebSocket editor (connection bar, stream inspector, composer, presets,
MCP preview sub-tab) but no user-visible way to start that editor from a blank workspace tab.
The tab bar and global shortcuts were built for HTTP requests only.

### Scope (this task)

- Audit all tab-creation and tab-restoration entry points.
- Document doc/code gaps.
- Assess MCP (WS-9) alignment at a product level.
- Define functional requirements and acceptance criteria for blank-tab WebSocket mode.
- Propose child implementation stories (requirements scope only — architecture is Step 2).

### Out of scope (this task)

- UI implementation, code changes, or architecture decisions (Step 2+).
- Changes to WS-9 bounded probe runtime behavior.
- History replay for WebSocket sessions (explicitly HTTP-only today; noted as a gap, not in
  epic scope unless a future story is opened).
- **Protocol switching on a blank, unsaved tab after creation (v1).** Users who chose the wrong
  protocol must close the tab and open a new one with the correct protocol at creation time.

### Tab Creation Flow Audit

| Entry point | Current behavior | WebSocket reachable? | Notes |
| --- | --- | --- | --- |
| **`Ctrl+N`** (`main_window.py` → `handle_new_tab("shortcut")`) | Always calls `add_new_tab()` → new HTTP `RequestTab` titled "New Request" | **No** | Documented in `doc/user/hotkeys.md` as "draft request tab" only |
| **Tab-bar `+` button** (`RequestTabHeader` → `handle_new_tab("plus_button")`) | Same as `Ctrl+N` | **No** | Tooltip: "New Tab (Ctrl+N)" — no protocol hint |
| **Collections left-click** on WebSocket item | `CollectionsPresenter.open_websocket_in_tab` → `TabsPresenter.open_websocket_tab(conn)` | **Yes** | Deduplicates by `connection.id`; only path for new WS tabs today |
| **Collections context menu → New tab** | Offered only when `item_type == "request"` (`collection_tree_actions.py`) | **No** | WebSocket items never get **New tab** |
| **Collections context menu → Rename / Delete** | `_resolve_item_target()` resolves `RequestData` and collection `str` only; **not** `WebSocketConnection` | **Broken** | Core strategies exist for `item_type == "websocket"` but the menu never resolves WS items |
| **History replay** (`HistoryPanel` → `load_request_from_history`) | Always `add_new_tab(request_data)` | **No** | Expected — history is HTTP request log |
| **Session restore on startup** (`restore_tabs` + `WebSocketRegistry.find_item`) | Restores both request and WebSocket tabs by saved item id | **Yes** | Opens restored WS tabs disconnected (`save_state=False`) |
| **Close last tab fallback** (`close_tab` when count → 0) | `add_new_tab(save_state=False)` → HTTP blank tab | **No** | User closing the only WS tab lands on HTTP editor |
| **Delete collection requests** (`close_tabs_for_request_ids`) | Closes HTTP tabs only; no symmetric `close_tabs_for_websocket_ids` | N/A | WebSocket tab lifecycle on profile delete not covered here |

### Supporting code facts (current state)

- `TabsPresenter.add_new_tab()` always constructs `RequestTab` via `_create_request_tab()`.
- `TabsPresenter.open_websocket_tab(connection)` requires an existing `WebSocketConnection`
  model instance; there is no `add_blank_websocket_tab()` equivalent.
- `TabsPresenter._current_tab()` returns `RequestTab | None` only — global shortcuts wired in
  `main_window.py` (Send, Focus URL, Params/Headers/Body/Script) silently no-op on WebSocket
  tabs.
- `WebSocketPresenter.connection_saved` is emitted from composer/presets panels but is **not**
  connected in `main_window_signals.py` — draft profile persistence from the WebSocket editor
  is incomplete relative to HTTP `RequestSaveOrchestrator`.
- `doc/user/hotkeys.md` documents a **WebSocket Session** shortcut group; `pypost/ui/hotkeys.py`
  `SECTION_ORDER` lists only General, Tabs, and Request Editor — WebSocket shortcuts are not
  registered in the live help dialog.

### Doc / Code Gap Analysis

| Source | States | Actual behavior | Severity |
| --- | --- | --- | --- |
| `doc/user/websocket.md` L13 | "Open a new tab and select the **WebSocket** mode" | No mode selector; blank tab is HTTP only | **Critical** — blocks documented onboarding |
| `doc/user/interface.md` L56 | "`Ctrl+N` / **+** opens a new tab" (generic) | Always HTTP `RequestTab` | **High** — implies parity with WebSocket editor section below |
| `doc/user/interface.md` L70–84 | Full WebSocket editor layout documented | Reachable only via Collections or restore | **High** |
| `doc/user/hotkeys.md` L20 | `Ctrl+N` → "draft **request** tab" | Accurate for code, inconsistent with `websocket.md` | **Medium** |
| `doc/user/hotkeys.md` L39–48 | WebSocket Session shortcuts (`Ctrl+S`, `F5`, etc.) | Not registered in `hotkeys.py`; global handlers skip WS tabs | **High** |
| `doc/user/collections.md` L25–28 | Click or right-click **New tab** for items | **New tab** missing for WebSocket; rename/delete menu broken | **High** |
| `doc/dev/websocket_ui_client.md` | Describes `open_websocket_tab(profile)` from Collections | Accurate; no blank-tab path documented | **Low** — dev doc matches code |
| `doc/dev/websocket_mcp_probe_tool.md` | MCP tools from saved profiles with `expose_as_mcp=True` | Accurate; interactive path to create profile not documented | **Medium** |
| Epic `PYPOST-1124` A-5.7 | Planned "WebSocket Session" hotkey section | Not implemented in `SECTION_ORDER` | **Medium** |
| `RequestTabHeader` | HTTP-oriented chrome only | No protocol indicator on tab strip | **Low** — expected until mode UX ships |

### MCP Alignment (WS-9) — Product Assessment

WS-9 (bounded MCP WebSocket probe, `doc/dev/websocket_mcp_probe_tool.md`) operates on **saved**
WebSocket profiles exposed via `expose_as_mcp=True`. The probe runtime is headless, bounded, and
does not share GUI tab state.

**Alignment conclusions (requirements level):**

1. **No shared "mode" runtime abstraction is required for MCP.** Agents invoke tools against
   persisted profiles; the probe does not care how the profile was authored.
2. **The GUI workflow must support: blank WebSocket tab → configure URL/headers/presets/MCP
   fields → Save to collection → enable MCP tool → verify contract in MCP preview sub-tab.**
   Today step 1 is missing, breaking the interactive half of the MCP story documented in
   `doc/user/websocket.md` (AI Assistant Integration) and `doc/user/mcp-tools.md`.
3. **Session slot governance (`ws_max_concurrent_sessions`) applies equally** to GUI tabs and MCP
   probes. A blank WebSocket draft tab that connects consumes a slot like any other session; UX
   copy should not imply otherwise.
4. **MCP preview sub-tab** already renders the agent contract for the in-tab profile. Once
   blank-tab creation exists, preview should work on unsaved drafts before first save
   (acceptance criterion for WS-TM-2).

### Main Entities (Business Perspective)

| Entity | Role in this feature |
| --- | --- |
| **Workspace tab** | Container in the tab strip holding either an HTTP request editor or a WebSocket session editor |
| **Protocol / mode** | User's choice between HTTP Request and WebSocket when starting a blank tab |
| **HTTP request draft** | Unsaved HTTP request in a workspace tab (today's default blank tab) |
| **WebSocket profile draft** | Unsaved WebSocket profile in a workspace tab (missing today) |
| **Saved WebSocket profile** | Persisted WebSocket profile in a collection; opens via the existing Collections path |
| **Collection tree item** | Sidebar node for a saved request or WebSocket profile |
| **MCP-exposed profile** | Saved WebSocket profile with MCP exposure enabled; consumed by WS-9 probe tools |

### Functional Requirements

#### FR-1: Blank-tab protocol selection

- FR-1.1 Users opening a new blank workspace tab (`Ctrl+N`, **+**, or empty-workspace fallback)
  must be able to start either an HTTP request draft or a WebSocket profile draft.
- FR-1.2 The chosen protocol must be visually obvious in the workspace (e.g., editor chrome
  matches `doc/user/interface.md` WebSocket vs Request sections).
- FR-1.3 **Protocol switching on a blank, unsaved tab after creation is out of scope for v1.**
  The user must close the tab or pick the correct protocol when the tab is created. Switching
  protocol on a tab that already has unsaved edits must confirm data loss (same standard as HTTP
  dirty-tab prompts) when such switching is supported in a future release.
- FR-1.4 **Default blank-tab protocol is HTTP** (matches current behavior). Opening a WebSocket
  draft requires an explicit user choice at tab creation.

#### FR-2: Blank WebSocket draft tab

- FR-2.1 A blank WebSocket tab presents the full WebSocket editor (connection bar, handshake
  tabs, stream inspector, composer) with a default name (e.g., "New WebSocket").
- FR-2.2 The draft is not written to a collection until the user explicitly saves.
- FR-2.3 Connect/Disconnect, messaging, presets, and stream inspection work on the draft the same
  as on a saved profile tab.
- FR-2.4 MCP preview sub-tab renders the agent contract for the in-tab draft configuration.
- FR-2.5 **Draft WebSocket tabs are not included in session restore until the user saves the
  profile to a collection.** Only saved profiles (and tabs restored from prior saved sessions)
  participate in startup session restore.

#### FR-3: Tab entry-point parity

- FR-3.1 `Ctrl+N`, tab-bar **+**, and close-last-tab fallback must all respect FR-1 (not
  hard-code HTTP).
- FR-3.2 Opening a saved WebSocket profile from Collections continues to use deduplicating focus
  behavior by profile id.
- FR-3.3 Session restore continues to reopen both HTTP and WebSocket tabs by saved item id
  without regression.

#### FR-4: Collections WebSocket menu parity

- FR-4.1 Right-click **New tab** on a WebSocket profile opens an isolated copy in a new tab,
  mirroring HTTP **New tab** semantics (independent edits, no shared live state).
- FR-4.2 Right-click **Rename** and **Delete** on WebSocket profiles function for WebSocket
  collection items.
- FR-4.3 Deleting a WebSocket profile closes or prompts on open tabs referencing that profile.

#### FR-5: WebSocket save flow

- FR-5.1 Users can **Save** and **Save As** a WebSocket draft to a collection (documented
  shortcuts `Ctrl+S` / `Ctrl+Shift+S`).
- FR-5.2 After save, the profile appears in the Collections tree and participates in MCP tool
  discovery when MCP exposure is enabled.
- FR-5.3 Save prompts, overwrite confirmation, and collection picker behavior match HTTP save
  UX expectations.
- FR-5.4 After a successful save, the workspace tab reflects the persisted profile (collection
  tree updates, tab title and identity align with the saved item).

#### FR-6: Context-aware shortcuts

- FR-6.1 When a WebSocket tab is active, global shortcuts documented under **WebSocket Session**
  in `doc/user/hotkeys.md` dispatch to WebSocket actions (Connect, Send, Save, Focus URL, etc.).
- FR-6.2 Help → Hotkeys lists the **WebSocket Session** section when WebSocket shortcuts are
  registered.

#### FR-7: Documentation truthfulness

- FR-7.1 `doc/user/websocket.md`, `doc/user/interface.md`, and `doc/user/hotkeys.md` describe
  the shipped blank-tab WebSocket workflow accurately after implementation stories complete.
- FR-7.2 User docs no longer reference a non-existent "WebSocket mode" control without describing
  where it lives.

### Non-Functional Requirements

- **NFR-1 Consistency:** Blank-tab WebSocket UX must feel analogous to blank-tab HTTP UX
  (create → compose → save → collection item).
- **NFR-2 Discoverability:** First-time users following `doc/user/websocket.md` must reach a
  WebSocket editor without undocumented steps.
- **NFR-3 Accessibility:** Protocol/state must not rely on color alone (consistent with existing
  WebSocket state badge rules).
- **NFR-4 Session limits:** Connecting from a blank WebSocket draft respects
  `ws_max_concurrent_sessions` like any other session.
- **NFR-5 Metrics:** New-tab actions should remain attributable by source and protocol in
  product telemetry.

### Constraints and Assumptions

- HTTP and WebSocket remain **separate editor experiences** in the workspace; this epic adds a
  user-facing **choice** at creation time, not a merged editor.
- History replay stays HTTP-only unless a separate future story is opened.
- WS-9 probe implementation is stable; this epic fixes the GUI authoring path, not probe bounds.
- Implementation stories must budget for existing module size constraints from PYPOST-1123
  (Step 2 concern).
- **v1 default blank-tab protocol is HTTP;** WebSocket requires explicit user choice at creation
  (see FR-1.4).

### Proposed Child Story Breakdown (Epic PYPOST-1155)

Stories use provisional IDs **WS-TM-1 … WS-TM-7** until Jira issues are created.

#### WS-TM-1: Blank-tab protocol selector UX

**Goal:** Users can choose HTTP Request vs WebSocket when opening a blank tab.

**Acceptance criteria:**

- `Ctrl+N` and **+** present a protocol choice (exact control deferred to Step 2 architecture).
- Default selection is HTTP; WebSocket is opt-in at creation.
- Choice is visible before the user enters a URL.
- New-tab actions are attributable by source and protocol in product telemetry.

#### WS-TM-2: Blank WebSocket draft tab

**Goal:** Users can open an unsaved WebSocket profile in a workspace tab without a saved
collection item.

**Acceptance criteria:**

- Blank WebSocket tab shows a default name and empty `ws://` URL field.
- Connect, stream, composer, presets, and MCP preview work on the draft.
- **Draft tabs are not persisted to session restore until the user performs a first save to a
  collection.**

#### WS-TM-3: Tab entry-point parity

**Goal:** All automatic new-tab paths respect protocol selection.

**Acceptance criteria:**

- Close-last-tab fallback uses the same protocol selection as `Ctrl+N`.
- Session restore behavior is unchanged for mixed HTTP/WebSocket workspaces (saved profiles only).
- No regression in session-restore scenarios for workspaces that mix HTTP and WebSocket tabs.

#### WS-TM-4: Collections WebSocket menu parity

**Goal:** Sidebar context menu works for WebSocket items.

**Acceptance criteria:**

- **New tab** opens an isolated WebSocket copy (independent from other open tabs).
- **Rename** / **Delete** work for WebSocket collection items.
- Open tabs react when a WebSocket profile is deleted from Collections.

#### WS-TM-5: WebSocket save-to-collection flow

**Goal:** Save / Save As for WebSocket drafts matches HTTP expectations.

**Acceptance criteria:**

- `Ctrl+S` / `Ctrl+Shift+S` and Actions menu save draft profiles to a collection.
- Saved item appears in the Collections tree without unnecessary full-tree refresh when possible.
- After save, the tab and Collections sidebar reflect the persisted profile.

#### WS-TM-6: Context-aware WebSocket shortcuts

**Goal:** Documented WebSocket hotkeys work when a WebSocket tab is focused.

**Acceptance criteria:**

- Global shortcuts dispatch to WebSocket actions when a WebSocket tab is active.
- Help → Hotkeys includes a **WebSocket Session** section matching registered shortcuts.
- Parity with `doc/user/hotkeys.md` WebSocket table.

#### WS-TM-7: User documentation alignment

**Goal:** User docs match shipped behavior.

**Acceptance criteria:**

- `doc/user/websocket.md` step 1 describes the real entry path.
- `doc/user/interface.md` clarifies protocol choice on new tab.
- `doc/user/hotkeys.md` matches registered shortcuts.
- `doc/user/collections.md` reflects WebSocket **New tab** support.

**Suggested implementation order:** WS-TM-1 → WS-TM-2 → WS-TM-3 → WS-TM-5 → WS-TM-6 →
WS-TM-4 → WS-TM-7 (WS-TM-4 can parallel WS-TM-5 once WS-TM-2 exists).

## Q&A

| Question | Answer |
| --- | --- |
| Does WS-9 need a "mode" abstraction? | **No** for runtime. MCP probes read saved profiles. GUI needs blank-tab authoring only. |
| Should history replay open WebSocket tabs? | **Out of scope** for PYPOST-1155. History is HTTP-shaped (status code and round-trip time). |
| What happens when the user closes the only WebSocket tab? | Today: HTTP blank tab appears. After WS-TM-3: should follow same protocol-selection rule as `Ctrl+N`. |
| Is Collections left-click sufficient without blank tab? | **Insufficient** — docs promise blank-tab mode; ad-hoc testing and MCP authoring require draft path. |
| Can the user switch protocol on a blank unsaved tab (v1)? | **No** — out of scope for v1. Close the tab and create a new one with the correct protocol. |
| What is the default protocol for a new blank tab (v1)? | **HTTP.** WebSocket requires an explicit choice at creation. |
| Are unsaved WebSocket draft tabs restored on restart? | **No** — session restore includes saved profiles only until the user saves the draft. |
| Epic planned unified tab open API — still relevant? | Conceptually yes; Step 2 will map to the current split between blank HTTP tabs and collection-opened WebSocket tabs. |

## References

- [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) — this research story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- `doc/user/websocket.md` (step 1 gap)
- `doc/user/interface.md`, `doc/user/hotkeys.md`, `doc/user/collections.md`
- `pypost/ui/presenters/tabs_presenter.py`, `pypost/ui/widgets/tab_header.py`
- `pypost/ui/presenters/collection_tree_actions.py`, `pypost/ui/main_window_signals.py`
- `doc/dev/websocket_mcp_probe_tool.md` (WS-9)
- `doc/dev/websocket_ui_client.md` (WS-4 tab lifecycle)
- `ai-tasks/PYPOST-1124/20-architecture.md` (A-5 interaction model, A-5.7 hotkeys)
