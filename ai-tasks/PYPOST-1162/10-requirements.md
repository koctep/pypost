# PYPOST-1162: WS-TM-6 — Context-aware WebSocket shortcuts

## Goals

Keyboard-driven users expect WebSocket session shortcuts documented in Help → Hotkeys
and `doc/user/hotkeys.md` to work when a WebSocket workspace tab is active. Today global
request-editor shortcuts either no-op or would target the wrong editor if a request tab
were coerced. This story closes the gap so WebSocket tabs behave like first-class peers
to HTTP request tabs for documented hotkeys.

## User Stories

- As a **keyboard-driven user**, I want Connect/Disconnect, Send, Save, Focus URL, and
  Format JSON shortcuts to work when my WebSocket tab is focused, so I can operate
  sessions without the mouse.
- As a **user reading Help → Hotkeys**, I want a **WebSocket Session** section listing
  registered shortcuts in the same order as user documentation.
- As a **user with mixed HTTP and WebSocket tabs**, I want request-editor shortcuts
  (Params, Headers, Body, Script) to do nothing when a WebSocket tab is active, so
  actions never silently apply to a hidden HTTP tab.

## Definition of Done

- [ ] `TabsPresenter` exposes tab-kind-aware handlers for connect, send, save, focus URL.
- [ ] `main_window._setup_shortcuts` registers **WebSocket Session** hotkeys per
  `doc/user/hotkeys.md`.
- [ ] `hotkeys.py` `SECTION_ORDER` includes **WebSocket Session**.
- [ ] Request-editor global shortcuts no-op when a WebSocket tab is active.
- [ ] Automated tests cover save dispatch, connect routing, focus URL, and section order.

## Task Description

Depends on WS-TM-2 (blank WebSocket draft tab) and WS-TM-5 (save entry points on
`WebSocketTab`). Save shortcuts were partially delivered in PYPOST-1161; this story
completes Connect, Send, Focus URL, Format JSON registration and context routing.

### Out of scope

- End-user doc prose updates (PYPOST-1163).
- MCP Client tab hotkeys (PYPOST-1175).
- Clear Stream shortcut (not in Jira acceptance criteria).

## Q&A

| Question | Answer |
| --- | --- |
| Why not register all WS shortcuts on `WebSocketTab` only? | Global F5/Ctrl+Return must route via `TabsPresenter` so request-editor handlers never fire on WS tabs; Help collects from main window tree. |
| Does Save need main_window registration? | Save/Save As remain on `WebSocketTab` actions (PYPOST-1161); Help collects via `findChildren(QAction)`. |
