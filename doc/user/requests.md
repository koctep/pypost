# Working with Requests

## Create a request

1. Press `Ctrl+N` or click **+** on the tab bar, then choose **HTTP Request** from the
   protocol picker.
2. Choose a method: **GET**, **POST**, **PUT**, **DELETE**, or **PATCH**.
3. Enter the URL. You can use environment variables, for example `{{ host }}/users`.
4. Configure **Params**, **Headers**, and **Body** as needed.
5. Click **Send**, or press `F5` / `Ctrl+Enter`.

Focus the URL bar with `Ctrl+L` or `Alt+D`. Switch editor tabs with `Ctrl+P` (Params),
`Ctrl+H` (Headers), `Ctrl+B` (Body), `Ctrl+T` (Script).

> **Outbound MCP:** To connect to a remote MCP server, list its tools, and invoke them
> interactively, use an **MCP Client** workspace tab — not an HTTP method. See the
> [MCP Client Guide](mcp-client.md).

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

## Hidden fields

On the **Hidden Fields** tab, configure response field selectors to mask sensitive
information (such as tokens, passwords, secret keys, or PII) returned by the API.

### Adding and managing selectors

- Enter a field name or path into the empty row at the bottom of the table. A new
  empty row appears automatically when you begin typing.
- Click **Add Selector** to add or jump to the trailing entry row.
- Select one or more rows and click **Remove Selected**, press `Delete` / `Backspace`,
  or right-click to use the context menu.
- Selectors are saved with the request draft and persist when saving to collections.

### Selector formats

| Format | Example | Description |
| --- | --- | --- |
| Simple key | `token`, `password` | Matches JSON keys with this name at any depth. |
| Dot-notation path | `auth.token`, `user.secret` | Matches exact hierarchical object paths. |
| Array wildcard path | `users[*].email` | Matches fields inside array elements. |

Masked fields protect confidential values during screen sharing and prevent sensitive data
from leaking when requests are executed by AI coding agents via MCP.

## Response

After send, the response pane shows:

- HTTP status
- Elapsed time
- Response size
- Response body

Very large response bodies may be truncated around 50 MB. This limit is built in;
there is no Settings control for it.

### Interacting with masked fields

When hidden fields are configured on the request, matching sensitive values in JSON responses
are masked by default as `"***"` with a neutral dashed underline:

- **Hover tooltips and cursor**: Hovering your mouse over a masked value changes the cursor to
  a pointing hand and displays a tooltip reading `Click to reveal`.
- **Click to reveal**: Left-click on the masked placeholder `"***"` to reveal the raw secret value
  in place. The visual styling changes to a subtle green background with a dotted underline, and
  the hover tooltip updates to `Click to re-mask`.
- **Click to re-mask**: Left-click the revealed value again at any time to re-mask the secret back
  to `"***"`.
- **Copying or setting variables**: You can highlight revealed text by clicking and dragging.
  Drag selection does not trigger a re-mask toggle. Right-click to open the context menu:
  - **Copy**: Copies the highlighted raw secret to your clipboard.
  - **Set Variable**: Saves the raw secret directly into an active environment variable
    (`Set Variable → <key>` or `New Variable...`).
- **Search synchronization**: Searching with `Ctrl+F` searches the rendered text. Revealing a
  masked secret makes it immediately searchable, and re-masking updates search matches accordingly.
- **Large responses**: Response payloads larger than 100 KB bypass interactive masking and render
  in plain text for optimal UI performance.

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
description and parameters on the **MCP** tab, then save. This is an **inbound** MCP surface
(PyPost exposes the request to agents). Details:
[MCP Tools for AI Agents](mcp-tools.md).

For **outbound** MCP (calling remote servers from PyPost), use the
[MCP Client Guide](mcp-client.md) instead.
