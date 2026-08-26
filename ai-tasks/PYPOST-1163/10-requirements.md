# PYPOST-1163: WS-TM-7 — User documentation alignment

## Goals

WebSocket tab mode features shipped in PYPOST-1157 through PYPOST-1162 (blank-tab protocol
picker, WebSocket draft tabs, collections **New tab**, save flow, context-aware shortcuts).
User-facing guides still describe the pre-tab-mode HTTP-only new-tab flow and omit collections
**New tab** behavior for WebSocket profiles. Readers following the docs cannot discover the
real entry paths or keyboard shortcuts.

This story aligns `doc/user/` with shipped behavior so help text, hotkeys reference, and
in-app **Help → Hotkeys** stay consistent.

## User Stories

- As a **new WebSocket user**, I want the WebSocket guide to describe how to open a blank
  WebSocket tab via the protocol picker, so I can start a session without guessing.
- As a **keyboard user**, I want `doc/user/hotkeys.md` to match registered WebSocket Session
  shortcuts, so offline reference matches **Help → Hotkeys**.
- As a **Collections user**, I want the collections guide to explain WebSocket **New tab**
  (isolated copy), so I know how sidebar actions differ from left-click open.

## Definition of Done

1. `doc/user/websocket.md` step 1 describes the real entry path (protocol picker on new tab
   and saved-profile paths).
2. `doc/user/interface.md` documents protocol choice on `Ctrl+N` and **+**.
3. `doc/user/hotkeys.md` matches registered WebSocket shortcuts (labels and keys).
4. `doc/user/collections.md` documents WebSocket **New tab** support.
5. Automated contract tests guard the four acceptance areas.

## Task Description

Docs-only alignment under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155). Depends on WS-TM-1 … WS-TM-6
(PYPOST-1157 … PYPOST-1162). Architecture reference:
`ai-tasks/PYPOST-1156/20-architecture.md`.

### Out of scope

- MCP Client tab mode user docs (PYPOST-1175 and follow-ups).
- Developer architecture rewrites (cross-links only in Step 8).
- Product behavior changes.

## Q&A

| Question | Answer |
| --- | --- |
| Why contract tests for prose? | Prevent regression when tab-mode docs drift from shipped UX again. |
| Must hotkey labels match Help exactly? | Yes — acceptance criteria require parity with registered actions. |
