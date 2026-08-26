# Collections

Collections group related requests and WebSocket profiles (for example by API or project)
in the left sidebar.

## Save a request or WebSocket profile

1. Configure the request or WebSocket profile in a tab.
2. Open **Actions** (to the right of **Send** / **Connect**) and choose **Save**, or press `Ctrl+S`.
3. In the dialog, pick an existing collection or create a new one.
4. Confirm. The item appears in the sidebar tree.

**Save As…** (`Ctrl+Shift+S`) always creates a new entry and leaves the original unchanged.

Settings may ask you to confirm before overwriting an existing saved item.

> [!WARNING]
> **Collection Downgrade Caveat:** Collections containing WebSocket profiles (`websockets` array)
> will lose their WebSocket configurations if opened and saved in older versions of PyPost that
> only support HTTP requests. Older versions do not preserve unrecognized fields upon saving.
> Always back up your collections before opening them in older PyPost versions.

## Open an item

- Click a request or WebSocket profile in the sidebar to open or focus it in the workspace
  (behavior depends on your click settings). Left-click on a WebSocket profile reuses one tab
  per saved profile id.
- Right-click a request or WebSocket profile and choose **New tab** to open a **separate
  editable copy** without replacing the current tab:
  - **HTTP requests** — isolated copy of the saved request (same semantics as before).
  - **WebSocket profiles** — isolated copy with its own live session; edits can be saved back
    to the same collection profile with **Save** (`Ctrl+S`) or forked with **Save As…**
    (`Ctrl+Shift+S`). See [WebSocket Guide](websocket.md).

Expand/collapse state of collections is remembered across sessions.

## Import a collection

Instead of recreating a teammate's requests and WebSocket profiles by hand, you can bring a whole
collection in from a file:

1. Click **Import Collection…** below the collection tree in the sidebar.
2. Pick a JSON file. It can contain:
   - A single collection as one JSON object, or
   - Several collections as a JSON list of objects.

   The expected shape is the same as PyPost's own `collections/<id>.json` — for example a
   file copied from another PyPost installation, or shared by a teammate:

   ```json
   {
     "name": "Billing API",
     "requests": [
       {
         "name": "Create invoice",
         "method": "POST",
         "url": "{{host}}/invoices",
         "headers": { "Authorization": "Bearer {{token}}" },
         "body": "{\"amount\": 100}",
         "body_type": "json"
       }
     ],
     "websockets": [
       {
         "name": "Live transaction stream",
         "url": "wss://{{host}}/transactions/stream",
         "headers": { "Authorization": "Bearer {{token}}" },
         "subprotocols": ["v1.events"]
       }
     ]
   }
   ```

   Only `name` is required. `requests` and `websockets` default to empty, and every field
   (`method`, `url`, `headers`, `params`, `body`, `body_type`, `post_script`, presets,
   sequences, retry policy, and MCP tool fields `expose_as_mcp`, `mcp_description`,
   `mcp_params`) is optional and carried through when present. `id` is optional — PyPost assigns
   a new one if it is missing or already in use.
3. If an imported collection's name matches one you already have, you are asked, per name,
   to **Overwrite** the existing one, **Keep Both** (the import is added as
   `Copy of <name>`, disambiguated further if that name is also taken), or **Skip** it.
   Check **Apply to all remaining conflicts** to use the same choice for every later
   conflict in the same import instead of being asked again.
4. When it finishes, a summary dialog shows how many collections were added, updated,
   skipped, or renamed, how many requests came in, and details for any entries that could
   not be imported. The sidebar tree refreshes automatically.

Notes:

- Large files keep the main window responsive while PyPost prepares the import. The status
  bar shows **Preparing collection import…** and **Import Collection…** stays disabled
  until prepare finishes; you can still use the rest of the app. Conflict prompts and the
  summary dialog appear afterward, as before.
- **Overwrite replaces a collection's requests wholesale** — it is not a per-request
  merge. The existing collection keeps its identity and position in the tree, but any
  request in it that is not in the imported file is gone. Choose **Keep Both** if you want
  to compare the two side by side first.
- If the file cannot be read at all, or contains no usable collections, your existing
  collections are left completely unchanged.
- One bad entry does not block the rest: an entry missing a `name`, or with a malformed
  request, is listed by name in the summary while its valid siblings still import.
- Imported requests marked **Expose as MCP tool** become available to agents as soon as
  the import finishes, without a restart. Check the names before importing a collection
  from someone else.
- Templating placeholders like `{{host}}` are imported as written. A request will not send
  correctly until the environment it expects is selected — see
  [Environments](environments.md).

Importing a collection is the reverse of copying a `collections/*.json` file out of your
data directory; PyPost does not currently read Postman, Insomnia, or OpenAPI files.

## Export a collection

To share or back up a collection without digging into the data directory:

1. Select the collection in the sidebar tree (or a request inside it — the parent
   collection is exported), then either:
   - Click **Export Collection…** below the tree, or
   - Right-click the collection or request row and choose **Export Collection…**.
2. Choose where to save the file. The default filename is based on the collection name.
3. When it finishes, a confirmation dialog shows the path and how many requests were
   exported.

The file is one JSON object with the same shape as **Import a collection** expects — a
direct copy of what PyPost stores in `collections/<id>.json`. You can send it to a
teammate or import it on another machine with **Import Collection…**.

Notes:

- If nothing is selected in the tree, export asks you to select a collection first.
- Every request field is included (`method`, `url`, `headers`, `params`, `body`,
  `body_type`, `post_script`, retry policy, and MCP tool settings), so the file
  round-trips through import without manual fixes.
- Export does not remove or change the collection in your sidebar — it only writes a
  copy to disk.

## Export all collections

To make one complete collection backup:

1. Click **Export All Collections…** below the collection tree. This action does not
   require selecting a collection or request first.
2. Choose the destination. The suggested filename is `collections.json`.
3. The confirmation dialog shows the saved path plus the number of collections and
   requests included. To restore the backup, use **Import Collection…** and choose this
   file; import accepts its JSON list directly.

An empty library is still exported successfully as an empty JSON list (`[]`). The backup
is non-destructive: it does not alter the collections or requests currently in the
sidebar. As with any collection export, the file can contain saved request values; store
or share it according to your data-sensitivity requirements.

## Rename and delete

Right-click a collection or request in the tree:

- **Export Collection…** — write the collection (or parent collection for a request) to a
  JSON file (same flow as the below-tree button)
- **Rename** — change the display name
- **Delete** — remove the item (you will be asked to confirm)

Deleting a collection removes its requests from the tree. Work carefully if those requests
are also marked as MCP tools.

## Example fixtures

Ready-to-import collections live under [`examples/collections/`](../../examples/README.md)
in the repo (see the [examples README](../../examples/README.md) for inventory, import
order, and secret rules). The curated **Jira Cloud MCP** collection is
`examples/collections/jira_mcp.json`; pair it with
`examples/environments/jira_cloud.json`. The tracked `examples/collections/mcp.json` file
is a local MCP/SSE probe for contributors, not the primary end-user starter.

Import with **Import Collection…** using the same steps as above — no format conversion.

## Tips

- Prefer short, stable request names if you expose them as MCP tools — agents see those
  names in `list_tools`.
- Keep environment-specific values in environments, not hard-coded in every request URL.
