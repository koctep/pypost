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
| New Tab | `Ctrl+N` | Opens a new draft request tab |
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

| Action | Shortcut | Description |
| ------ | -------- | ----------- |
| Connect / Disconnect | `F5` / `Ctrl+Enter` | Toggles connection state from URL bar |
| Send Message | `Ctrl+Enter` | Sends active message from Composer |
| Save Profile | `Ctrl+S` | Saves WebSocket profile to collection |
| Save As Profile | `Ctrl+Shift+S` | Saves draft to a new collection profile |
| Format JSON | `Ctrl+Shift+F` | Formats and validates JSON payload |
| Focus URL Bar | `Ctrl+L` / `Alt+D` | Highlights WebSocket URL input |

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
