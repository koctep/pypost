# Collections

Collections group related requests (for example by API or project) in the left sidebar.

## Save a request

1. Configure the request in a tab.
2. Open **Actions** (to the right of **Send**) and choose **Save**, or press `Ctrl+S`.
3. In the dialog, pick an existing collection or create a new one.
4. Confirm. The request appears in the sidebar tree.

**Save As…** (`Ctrl+Shift+S`) always creates a new entry and leaves the original unchanged.

Settings may ask you to confirm before overwriting an existing saved request.

## Open a request

- Click a request in the sidebar to open it in the editor (behavior depends on your click
  settings).
- Right-click a request and choose **New tab** to open a separate editable copy without
  replacing the current tab.

Expand/collapse state of collections is remembered across sessions.

## Import a collection

Instead of recreating a teammate's requests by hand, you can bring a whole collection —
with all of its requests — in from a file:

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
     ]
   }
   ```

   Only `name` is required. `requests` defaults to empty, and every request field
   (`method`, `url`, `headers`, `params`, `body`, `body_type`, `post_script`, retry
   policy, and the MCP tool fields `expose_as_mcp`, `mcp_description`, `mcp_params`) is
   optional and carried through when present. `id` is optional — PyPost assigns a new one
   if it is missing or already in use.
3. If an imported collection's name matches one you already have, you are asked, per name,
   to **Overwrite** the existing one, **Keep Both** (the import is added as
   `Copy of <name>`, disambiguated further if that name is also taken), or **Skip** it.
   Check **Apply to all remaining conflicts** to use the same choice for every later
   conflict in the same import instead of being asked again.
4. When it finishes, a summary dialog shows how many collections were added, updated,
   skipped, or renamed, how many requests came in, and details for any entries that could
   not be imported. The sidebar tree refreshes automatically.

Notes:

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

1. Click a **collection name** in the sidebar tree (or a request inside it — the parent
   collection is exported).
2. Click **Export Collection…** below the tree.
3. Choose where to save the file. The default filename is based on the collection name.
4. When it finishes, a confirmation dialog shows the path and how many requests were
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

## Rename and delete

Right-click a collection or request in the tree:

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
