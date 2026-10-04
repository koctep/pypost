# PYPOST-1285: Disambiguate Ctrl+Enter shortcut routing and documentation across protocol tabs

## Goals

PyPost users work with three kinds of tabs: HTTP Request, WebSocket, and MCP Client. In the
WebSocket and MCP Client tabs, the same key combination, `Ctrl+Enter`, does two very different
things depending on where the keyboard focus happens to be:

- WebSocket tab: it sends the composed message when the message composer has focus, but it
  connects or disconnects the session when focus is anywhere else.
- MCP Client tab: it invokes the selected tool when the arguments form has focus, but it
  connects or disconnects the session when focus is anywhere else.

The documentation and the in-app **Help → Hotkeys** dialog repeat this ambiguity by listing
`Ctrl+Enter` under both **Connect / Disconnect** and **Send Message** / **Invoke Tool**.

This has real costs for the user:

- **Unintended disconnects.** A user who expects `Ctrl+Enter` to send a message or invoke a
  tool can drop a live session (and lose subscriptions, stream position, or server state) just
  because focus moved out of the composer or form, for example after clicking the message
  stream or a preset.
- **Unintended connections.** The same press can open a session to a server the user did not
  mean to contact yet.
- **No reliable mental model.** One shortcut that means two opposite things, depending on focus
  the user cannot always see, cannot be learned or trusted. The documentation does not settle
  the question either.

The business goal is a predictable keyboard model with exactly one meaning per shortcut:
`Ctrl+Enter` sends or invokes, and `F5` connects or disconnects. Users should be able to learn
this from **Help → Hotkeys** and from the user documentation, and both should match what the
application actually does.

## Programming Language

- **Implementation language**: Python (per `ai-tasks/PYPOST-1285/00-roadmap.md`). PyPost is a
  PySide6/Qt desktop application. The user documentation that has to be aligned is Markdown.

## Business Entities

- **Protocol tab**: a workspace tab of one kind: HTTP Request, WebSocket, or MCP Client.
- **Session (WebSocket / MCP Client)**: the live connection a WebSocket or MCP Client tab
  holds. Its states are disconnected, connecting, connected/open, and (for WebSocket)
  reconnecting.
- **Primary action**: the main "do it" action of a tab. For HTTP it is **Send Request**, for
  WebSocket it is **Send Message** (the current composer content), and for MCP Client it is
  **Invoke Tool** (the selected tool with the current arguments).
- **Connection action**: **Connect / Disconnect**. It connects when the session is not active
  and disconnects (or cancels an attempt in progress) when it is. Only WebSocket and MCP Client
  tabs have it.
- **Hotkey reference**: the in-app **Help → Hotkeys** dialog plus the user documentation
  (`doc/user/hotkeys.md` and the protocol guides that mention these shortcuts, such as
  `doc/user/websocket.md`).

## User Stories

- As a WebSocket user, I want `Ctrl+Enter` to always mean "send the message", so that I never
  drop or open a connection by accident because focus left the composer.
- As an MCP Client user, I want `Ctrl+Enter` to always mean "invoke the selected tool", so that
  I never drop or open a session to the MCP server by accident.
- As a WebSocket or MCP Client user, I want `F5` to always mean "Connect / Disconnect", so that
  I have one dedicated, predictable key for controlling the session, wherever focus is in the
  tab.
- As an HTTP Request user, I want `F5` and `Ctrl+Enter` to keep sending the request, so that my
  existing workflow does not change.
- As any user, I want **Help → Hotkeys** to list each shortcut under exactly one action per tab
  kind, so that I can learn the keyboard model from the app itself.
- As any user reading the user documentation, I want the shortcut descriptions to match
  **Help → Hotkeys** and the real behavior, so that I can trust the docs.

## Definition of Done

### Shortcut behavior

1. **WebSocket tab, `Ctrl+Enter`**: triggers only the Send Message action, wherever keyboard
   focus is inside the tab. It never connects, disconnects, or cancels a connection attempt.
2. **WebSocket tab, `Ctrl+Enter` when no message can be sent** (session not open, or the
   message is rejected by the existing send rules): no message is sent, and the session state
   does not change. The existing behavior for a blocked send is kept, with no new dialog or
   error.
3. **MCP Client tab, `Ctrl+Enter`**: triggers only the Invoke Tool action, wherever keyboard
   focus is inside the tab. It never connects or disconnects the session.
4. **MCP Client tab, `Ctrl+Enter` when no tool can be invoked** (not connected, no tool
   selected, or invalid arguments): no invocation happens, and the session state does not
   change. The existing behavior for a blocked invoke is kept.
5. **WebSocket and MCP Client tabs, `F5`**: triggers only Connect / Disconnect, wherever
   keyboard focus is in the tab, including the message composer and the tool arguments form.
   It never sends a message or invokes a tool.
6. **HTTP Request tab**: `F5` and `Ctrl+Enter` both still trigger Send Request, as they do
   today.
7. All other shortcuts (Focus URL Bar, Save / Save As, Format JSON, tab navigation, request
   editor shortcuts, and so on) behave as they do today.
8. The on-screen buttons (Connect / Disconnect, Send, Invoke) behave as they do today. Only
   keyboard routing changes.

### Help → Hotkeys dialog

9. In the **WebSocket Session** section, **Connect / Disconnect** lists only `F5`, and
   **Send Message** lists only `Ctrl+Enter` (shown with the platform-native key name).
10. In the **MCP Client** section, **Connect / Disconnect** lists only `F5`, and
    **Invoke Tool** lists only `Ctrl+Enter`.
11. The **Request Editor** section still lists **Send Request** with `F5` and `Ctrl+Enter`.
12. Within one tab kind's section, no key combination is listed under more than one action.

### User documentation

13. `doc/user/hotkeys.md` matches items 9 to 11. Each shortcut appears under exactly one
    action per tab kind, and the descriptions no longer say "Send when Composer is focused" or
    "Invoke when args form focused" (or anything similar) for Connect / Disconnect.
14. The other user guides stop describing `Ctrl+Enter` as a way to connect. In particular,
    `doc/user/websocket.md` must say that `F5` connects and disconnects and that `Ctrl+Enter`
    sends.
15. User documentation, **Help → Hotkeys**, and the actual behavior all agree.

### Quality

16. Automated tests cover the new routing for both WebSocket and MCP Client tabs: `Ctrl+Enter`
    and `F5`, with focus inside and outside the composer or arguments form, and the connected
    and disconnected states. They also confirm that HTTP Request tab behavior has not changed.
17. `make check` passes.

## Task Description

### Problem

There is one global shortcut binding for the tab's primary action. In WebSocket and MCP Client
tabs it routes to either the primary action or the connection action depending on keyboard
focus, and it does this for both `F5` and `Ctrl+Enter`. As a result:

- `Ctrl+Enter` can change connection state, which users do not expect from a send/invoke key.
- `F5` can send a message or invoke a tool when the composer or arguments form has focus, which
  contradicts F5's documented role as the connection key.
- The documentation and the Help dialog list `Ctrl+Enter` under two conflicting actions.

### Scope: in

- Keyboard routing of `Ctrl+Enter` and `F5` in WebSocket and MCP Client tabs, so each key has
  exactly one meaning: `Ctrl+Enter` sends or invokes, and `F5` connects or disconnects.
- Keeping HTTP Request tab behavior for `F5` and `Ctrl+Enter` the same.
- Updating the **WebSocket Session** and **MCP Client** rows in **Help → Hotkeys**.
- Updating `doc/user/hotkeys.md` and any other user guide in `doc/user/` that describes these
  shortcuts the old way (for example, `doc/user/websocket.md`).
- Updating developer documentation in `doc/dev/` that describes the routing (for example, the
  WebSocket and MCP Client hotkey pages), as part of the workflow's dev-docs step.

### Scope: out

- Making shortcuts user-configurable, or adding or removing other shortcuts.
- Changing what Send Message, Invoke Tool, Send Request, or Connect / Disconnect do once they
  are triggered, including their preconditions and validation.
- Changing how `Enter` / `Ctrl+Enter` edit text inside multi-line editors, beyond the routing
  described above.
- Changing on-screen buttons, menus, or tooltips, except where they state the old,
  contradictory shortcut mapping.

### Constraints and assumptions

- `F5` remains the dedicated Connect / Disconnect shortcut in WebSocket and MCP Client tabs
  (stated in the Jira ticket).
- Shortcuts apply only while the matching tab kind is active. Behavior with no tab open does
  not change.
- On macOS, the key names follow the platform-native display that **Help → Hotkeys** already
  uses.

### Non-functional requirements

- **Predictability**: within a tab kind, a shortcut's effect depends only on the tab kind (and
  on the existing preconditions of the action it triggers), never on which widget has focus.
- **Safety**: no shortcut other than `F5` (and the explicit buttons) may change the connection
  state of a WebSocket or MCP Client session.
- **Consistency**: the in-app Help dialog and the user documentation are the source of truth
  for users, and they must match the behavior.

## Q&A

- **Q: When focus is outside the composer (WebSocket) or the arguments form (MCP Client),
  should `Ctrl+Enter` do nothing, or still send / invoke?**
  A: It should still send or invoke. **Help → Hotkeys** presents Send Message and Invoke Tool as
  tab-level shortcuts, and the ticket says `Ctrl+Enter` should "only send / invoke". Making it
  depend on focus would keep the ambiguity the ticket is meant to remove. Sending is already
  guarded by the existing preconditions (an open session, a valid message or arguments), so an
  accidental press cannot change connection state. The architecture step can revisit this
  decision if it conflicts with the existing widget structure, but the "never toggles the
  connection" rule is not negotiable.
- **Q: Should `F5` still send a message or invoke a tool while the composer or arguments form
  has focus (as it does today)?**
  A: No. The ticket makes `F5` the dedicated Connect / Disconnect shortcut, and the
  disambiguation applies in both directions: `F5` never sends or invokes in WebSocket and MCP
  Client tabs.
- **Q: Does anything change for HTTP Request tabs?**
  A: No. HTTP tabs have no connection action, so `F5` and `Ctrl+Enter` both stay as Send
  Request.
- **Q: What happens when `Ctrl+Enter` is pressed in a disconnected WebSocket or MCP Client
  tab?**
  A: Nothing is sent or invoked, and the tab does not connect. The existing blocked-send or
  blocked-invoke behavior applies.
- References: Jira PYPOST-1285; current user docs `doc/user/hotkeys.md`, `doc/user/websocket.md`;
  current dev docs `doc/dev/websocket_hotkeys.md`, `doc/dev/mcp_client_hotkeys.md`.
