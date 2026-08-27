# PYPOST-1175: MCP-TM-9 — Context-aware MCP Client shortcuts

## Goals

Keyboard-driven users expect MCP Client session shortcuts to work when an MCP Client
workspace tab is active, matching the WebSocket shortcut pattern delivered in PYPOST-1162.
Today global request-editor shortcuts no-op on MCP Client tabs because routing only targets
HTTP request tabs.

## User Stories

- As a **keyboard-driven user**, I want Connect/Disconnect, Invoke, Save, and Focus URL
  shortcuts to work when my MCP Client tab is focused.
- As a **user reading Help → Hotkeys**, I want an **MCP Client** section listing registered
  shortcuts in the same order as user documentation.
- As a **user with mixed HTTP and MCP Client tabs**, I want request-editor shortcuts to do
  nothing when an MCP Client tab is active.

## Definition of Done

- [x] `TabsPresenter` exposes tab-kind-aware handlers for connect, invoke, save, focus URL.
- [x] `main_window._setup_shortcuts` registers **MCP Client** help rows per `doc/user/hotkeys.md`.
- [x] `hotkeys.py` `SECTION_ORDER` includes **MCP Client**.
- [x] Request-editor global shortcuts no-op when an MCP Client tab is active.
- [x] Automated tests cover save dispatch, connect routing, invoke routing, focus URL, section order.

## Task Description

Depends on MCP-TM-2 blank MCP Client tab (PYPOST-1166) and WS-TM-6 tab-kind routing
(PYPOST-1162). Save shortcuts were partially tagged on `McpClientTab`; this story completes
Connect, Invoke, Focus URL registration and context routing.

### Out of scope

- SSE, prompts/resources, protocol trace, stdio stretch items.
- Changes to outbound MCP presenter metrics (unchanged).

## Q&A

| Question | Answer |
| --- | --- |
| Why mirror WebSocket routing? | Same `TabsPresenter.active_tab_kind()` pattern; users expect F5/Ctrl+Enter semantics across protocol tabs. |
| Does Save need main_window registration? | Save/Save As remain on `McpClientTab` actions; Help collects via `findChildren(QAction)`. |
