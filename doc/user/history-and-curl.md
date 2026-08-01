# History and Copy cURL

## History

The sidebar **History** tab lists executed requests (newest first). Each row shows
method, timestamp, status code, and the resolved URL.

Typical actions:

- **Filter by URL…** — type in the filter box to narrow the list
- Select a row to inspect **Method**, **URL**, **Status**, **Time**, **Headers**, and
  **Body** in the detail pane
- **Load into Editor** — copy the selected entry's method, URL, headers, and body into
  the request editor
- Right-click → **Delete** — remove one entry
- **Clear All** — wipe the entire history (confirmation required)
- Right-click → **Copy as cURL**, or select a row and press `Cmd/Ctrl+C`

History stores the **resolved** request that was sent. Values derived from **hidden**
environment variables are redacted before storage (and heuristic redaction may mask
tokens in URLs, headers, and bodies). Prefer hidden variables for secrets so they do
not land in `history.json` in clear text.

History is capped (hundreds of entries); older rows drop off automatically.

## Copy cURL from the editor

1. Configure the request and select the right environment.
2. Open **Actions → Copy cURL**.
3. Paste into a terminal.

The command includes method, URL, headers, and body with templates resolved from the
**active** environment. Params from the **Params** tab are merged into the URL query
string. If **YAML as JSON** is enabled for a YAML body, the cURL body uses the JSON
wire form.

If a variable or function expression cannot be resolved, fix the environment (or the
placeholder) and copy again.

## When to use which

| Goal | Use |
| ---- | --- |
| Reproduce the draft you are editing | **Actions → Copy cURL** |
| Reproduce exactly what was last sent | History → **Copy as cURL** |
| Share a one-liner with a teammate | Either, after resolving secrets carefully |

Do not paste cURL commands that contain real secrets into public channels. Prefer
hidden variables and redact tokens before sharing.
