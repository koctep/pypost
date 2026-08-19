# Environments

Environments store named sets of variables (hosts, tokens, API keys) so you can switch
between configurations such as `Local`, `Dev`, and `Prod` without editing every request.

## Manage environments

1. Click **Manage** in the top bar, or press `Ctrl+E`.
2. Add an environment with **+**.
3. Select it in the list.
4. Edit the variables table: **Variable**, **Value**, **Hidden**.
5. The **Enable MCP Server** toggle is retained only for legacy migration. To expose
   requests now, use **MCP Servers…** to create a row that selects this environment
   and one collection.
6. Save.

You can rename (for example with F2 or the context menu), copy, and delete environments
from the list.

## Import environments

Instead of retyping every host, token, and API key by hand, you can bring in one or more
environments from a file:

1. In **Manage Environments**, click **Import…** next to **Add**.
2. Pick a JSON file. It can contain:
   - A single environment as one JSON object, or
   - Several environments as a JSON list of objects.

   The expected shape is the same as PyPost's own `environments.json` — for example, a file
   exported by copying it from another PyPost installation, or shared by a teammate:

   ```json
   [
     {
       "name": "Staging",
       "variables": { "host": "https://staging.example.com", "token": "abc123" },
       "hidden_keys": ["token"],
       "enable_mcp": false
     }
   ]
   ```

   `name` and `variables` are required; `hidden_keys` (which variable names are **Hidden**)
   and `enable_mcp` are optional and default to none/off. `id` is optional — PyPost assigns
   a new one if it is missing.
3. If an imported environment's name matches one you already have, you are asked, per
   name, to **Overwrite** the existing one, **Keep Both** (the import is added as
   `Copy of <name>`, disambiguated further if that name is also taken), or **Skip** it.
   Check **Apply to all remaining conflicts** to use the same choice for every later
   conflict in the same import instead of being asked again.
4. When it finishes, a summary dialog shows how many environments were added, updated,
   skipped, or renamed, plus details for any entries that could not be imported.

Notes:

- Variables marked **Hidden** in the file stay **Hidden** after import, and are protected
  by your current [encryption at rest](#encryption-at-rest-optional) setting exactly like
  any other Hidden variable — importing never exposes or downgrades a secret.
- If the file contains a Hidden value that was encrypted by a *different* installation
  (a different encryption key), that specific entry fails with a clear error naming the
  environment; the rest of the file still imports normally.
- If the file cannot be read at all, or contains no usable environments, your existing
  environments are left completely unchanged.
- Import only reads a file — it does not change anything until you see the summary
  dialog. You can also **export** environments from the same screen (see below).

## Export environments

Save one or all environments to a JSON file you can import elsewhere or keep as a backup:

1. In **Manage Environments**, click **Export…** next to **Import…**.
2. Choose **Selected Environment** (the row highlighted in the list) or **All
   Environments**.
3. If the export includes any **Hidden** variables, PyPost asks you to confirm —
   the saved file will contain those secret values (see
   [Hidden policy](#hidden-values-in-export-files) below).
4. Pick where to save the file. One environment is written as a single JSON object;
   several environments are written as a JSON list — the same shapes **Import…** accepts.
5. A summary dialog confirms what was exported and where it was saved.

The file format matches PyPost's native `environments.json` records (the same format
described in [Import environments](#import-environments) above), so export and import
round-trip on the same installation.

### Hidden values in export files

PyPost **includes Hidden variable values in the export file** (not redacted) so the
file can be imported back without re-entering secrets. Before writing, you must confirm
when any exported environment has Hidden variables.

- When [encryption at rest](#encryption-at-rest-optional) is **off**, Hidden values are
  stored as plaintext strings in the file.
- When encryption is **on**, Hidden values are stored as encrypted envelopes in the
  file — the same representation as in your local `environments.json`. Those envelopes
  import correctly on **this** installation; on another machine with a different
  encryption key, import reports a clear error for that entry (see Import notes above).

Treat exported files like credential backups: store and share them carefully.

## Activate an environment

Choose it in the top dropdown. GUI request `{{ variable }}` placeholders use the
**currently selected** environment.

MCP tool calls use the environment selected in their own **MCP Servers…** row. Switching
the top-bar selection does not retarget a running endpoint. Edit the endpoint row when an
agent should use a different environment.

## Hidden variables

Mark sensitive keys (tokens, passwords) as **Hidden**:

- Values show as `********` in the UI and hover previews
- Real values are still used when sending requests and when MCP tools run
- Hidden-derived values are masked in history storage

Right-click a variable row to delete it when needed.

## Encryption at rest (optional)

In **Settings**, you can enable encryption for environment data on disk. Only variables
marked **Hidden** are encrypted in `environments.json`; non-hidden values remain
plaintext.

Configure key source (environment variable, OS keyring, or secret store) and use the
migration actions in Settings if you change encryption mode. See [Settings](settings.md).

## Example fixtures

Companion example environments live under
[`examples/environments/`](../../examples/README.md) (see the
[examples README](../../examples/README.md) for inventory, recommended import order, and
placeholder/secret rules). Start with `examples/environments/jira_cloud.json`: replace
`jira_base_url` and the hidden `jira_credentials` placeholder with your own site URL and
`email:api_token` after import — never commit real tokens.

Import with **Manage Environments → Import…** using the same steps as above.

## Using variables in requests

See [Templating](templating.md). Example: set `host` = `https://api.example.com`, then use
`{{ host }}/users` in the URL field.
