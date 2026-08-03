# Interface

The main window is divided into these areas:

## Menu bar

- **File → Quit** (`Ctrl+Q`) — exit the application
- **Help → Hotkeys** — list of keyboard shortcuts
- **Help → About** — application information

## Environment panel (top bar)

- **Environment dropdown** — selects the active environment used for GUI request variable
  substitution; it does not retarget a configured MCP endpoint
- **Manage** (`Ctrl+E`) — open the environment manager
- **MCP Servers…** — create and manage independent endpoints, each with its own collection,
  environment, host, port, status, tools, and activity
- **MCP status** — aggregate running/failed server count; open **MCP Servers…** for a
  row's endpoint and error details
- **MCP Server Tools…** — opens the manager so tools are inspected for one selected server

## Sidebar (left)

- **Collections** — tree of collections and saved requests
- **History** — log of executed requests

Right-click items in the collections tree for actions such as open in a new tab, rename,
or delete.

## Workspace (right)

Tabs with request editors. Each tab holds one draft request (method, URL, params,
headers, body, script, optional MCP metadata).

- Click **+** or press `Ctrl+N` to open a new tab
- Close with `Ctrl+W`
- Switch tabs with `Ctrl+Tab` / `Ctrl+Shift+Tab`, or `Alt+1` … `Alt+9`

## Request editor

From top to bottom in a typical layout:

1. Method combo, URL field, **Send**, **Actions** menu
2. Tabs: **Params**, **Headers**, **Body**, **Script**, and **MCP** (when relevant)
3. Response pane: status, time, size, body, and search (`Ctrl+F`)

**Actions** includes **Save As...**, **Save**, and **Copy cURL**.

## Settings

Open with `Ctrl+,` or `F12`. See [Settings](settings.md).
