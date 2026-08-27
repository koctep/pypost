# Hotkeys

In the app, open **Help → Hotkeys** for the live list (platform-native key names).
Shortcuts are grouped by scope:

## General application shortcuts

Global shortcuts accessible from any view:

| Action | Shortcut | Description |
| ------ | -------- | ----------- |
| Quit Application | `Ctrl+Q` | Closes PyPost cleanly |
| Settings | `Ctrl+,` / `F12` | Opens global Preferences dialog |
| Environment Manager | `Ctrl+E` | Opens Manage Environments dialog |

## Tabs & workspace navigation

| Action | Shortcut | Description |
| ------ | -------- | ----------- |
| New Tab | `Ctrl+N` | Opens the protocol picker (HTTP Request, WebSocket, or MCP Client) |
| Close Tab | `Ctrl+W` | Closes the active tab |
| Next Tab | `Ctrl+Tab` | Cycles forward through open tabs |
| Previous Tab | `Ctrl+Shift+Tab` | Cycles backward through open tabs |
| Switch to Tab 1-9 | `Alt+1` … `Alt+9` | Jumps directly to tab by index |

## Request composer

| Action | Shortcut | Description |
| ------ | -------- | ----------- |
| Send Request | `F5` / `Ctrl+Enter` | Executes the active request |
| Save Request | `Ctrl+S` | Saves request changes to collection |
| Save As Request | `Ctrl+Shift+S` | Saves draft to a new collection item |
| Focus URL Bar | `Ctrl+L` / `Alt+D` | Highlights the request URL input |
| Switch to Params | `Ctrl+P` | Activates Query Parameters tab |
| Switch to Headers | `Ctrl+H` | Activates Headers tab |
| Switch to Body | `Ctrl+B` | Activates Request Body tab |
| Switch to Script | `Ctrl+T` | Activates Post-Request Script tab |

## WebSocket session

Active when a WebSocket tab is focused. **Help → Hotkeys** lists **Save WebSocket Profile**
and **Save As WebSocket Profile** only while a WebSocket tab exists in the workspace.

| Action | Shortcut | Description |
| ------ | -------- | ----------- |
| Connect / Disconnect | `F5` / `Ctrl+Enter` | Connect from URL bar; Send when Composer is focused |
| Send Message | `Ctrl+Enter` | Sends the active message from the Composer |
| Save WebSocket Profile | `Ctrl+S` | Saves the WebSocket profile to a collection |
| Save As WebSocket Profile | `Ctrl+Shift+S` | Saves to a new collection profile |
| Focus URL Bar | `Ctrl+L` / `Alt+D` | Highlights the WebSocket URL input |
| Format JSON | `Ctrl+Shift+F` | Formats and validates JSON in the Composer |

Request-editor shortcuts (Params, Headers, Body, Script) do nothing when a WebSocket tab is
active.

## MCP Client session

Active when an **MCP Client** tab is focused. **Help → Hotkeys** lists **Save MCP Client
Profile** and **Save As MCP Client Profile** only while an MCP Client tab exists in the
workspace.

| Action | Shortcut | Description |
| ------ | -------- | ----------- |
| Connect / Disconnect | `F5` / `Ctrl+Enter` | Connect from URL; Invoke when args form focused |
| Invoke Tool | `Ctrl+Enter` | Invokes the selected remote tool with current arguments |
| Save MCP Client Profile | `Ctrl+S` | Saves the MCP Client profile to a collection |
| Save As MCP Client Profile | `Ctrl+Shift+S` | Saves to a new collection profile |
| Focus URL Bar | `Ctrl+L` / `Alt+D` | Highlights the MCP Client URL input |

Request-editor shortcuts (Params, Headers, Body, Script) do nothing when an MCP Client tab is
active.

## Body editor & response viewer shortcuts

Context-sensitive shortcuts active when specific panes have focus:

### Body editor

- `Ctrl+Z` / `Ctrl+Y` — Undo and redo edits in the raw request payload editor.
- `Tab` / `Shift+Tab` — Indent and unindent selected text blocks.
- `Ctrl+A` — Select entire editor content.

### Response pane

- `Ctrl+F` — Open in-response search bar.
- `F3` / `Shift+F3` — Jump to next / previous match in the response body.
- `Esc` — Close response search bar and clear highlight.

### History sidebar

- `Ctrl+C` / `Cmd+C` — Copy selected historical request as an executable `curl` command.

## macOS modifier keys

On macOS, `Ctrl` shortcuts map to the Command key (`Cmd` / `⌘`) where standard:
`Cmd+Q` (Quit), `Cmd+,` (Settings), `Cmd+N` (New Tab), `Cmd+W` (Close Tab), and
`Cmd+Enter` (Send Request). Check **Help → Hotkeys** in-app for your platform's exact bindings.
