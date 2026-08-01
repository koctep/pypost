# Working with Requests

## Create a request

1. Press `Ctrl+N` or click **+** on the tab bar.
2. Choose a method: **GET**, **POST**, **PUT**, **DELETE**, **PATCH**, or **MCP**.
   Use **MCP** when calling MCP endpoints from PyPost itself.
3. Enter the URL. You can use environment variables, for example `{{ host }}/users`.
4. Configure **Params**, **Headers**, and **Body** as needed.
5. Click **Send**, or press `F5` / `Ctrl+Enter`.

Focus the URL bar with `Ctrl+L` or `Alt+D`. Switch editor tabs with `Ctrl+P` (Params),
`Ctrl+H` (Headers), `Ctrl+B` (Body), `Ctrl+T` (Script).

## Parameters and headers

On the **Params** and **Headers** tabs, use the key-value table:

- Enter a key and a value in a row
- A new empty row appears when you fill the last one
- Values support `{{ variable }}` placeholders (see [Templating](templating.md))

Query parameters are applied to the URL when the request is sent.

## Request body

On the **Body** tab, enter the payload (JSON, YAML, XML, or plain text).

Useful editor features:

- Format selection (JSON / YAML / XML) with validation where applicable
- Line numbers, folding, and indentation helpers
- Optional **YAML as JSON**: convert YAML to JSON on send; paste JSON as YAML in the
  editor when enabled
- Changing to a body-oriented method may auto-focus the Body tab

Hover over `{{ ... }}` placeholders to preview the resolved value (hidden variables stay
masked).

## Response

After send, the response pane shows:

- HTTP status
- Elapsed time
- Response size
- Response body

Very large response bodies may be truncated around 50 MB. This limit is built in;
there is no Settings control for it.

### Search in the response

- Press `Ctrl+F` to focus the search field
- Use **Next** / **Previous** or Enter to move between matches
- Enable **Match case** for case-sensitive search
- The counter shows the current match (for example `2 of 5`)

## Save

- **Actions → Save** (`Ctrl+S`) — save into a collection (create or overwrite)
- **Actions → Save As...** (`Ctrl+Shift+S`) — always create a new saved request

See [Collections](collections.md).

## Copy as cURL

**Actions → Copy cURL** copies a shell-ready `curl` command with variables resolved from
the active environment. See [History and Copy cURL](history-and-curl.md).

## MCP Tool checkbox

Check **MCP Tool** next to the URL bar to expose this saved request to AI agents. Configure
description and parameters on the **MCP** tab, then save. Details:
[MCP Tools for AI Agents](mcp-tools.md).
