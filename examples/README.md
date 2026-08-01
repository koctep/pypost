# Example collections and environments

Importable fixtures you can load into PyPost, fill with your own values, and adapt.
They use the same native JSON shapes as **Import Collection…** and
**Manage Environments → Import…**.

For step-by-step import UI details, see the User Guide:

- [Import a collection](../doc/user/collections.md#import-a-collection)
- [Import environments](../doc/user/environments.md#import-environments)
- [MCP tools](../doc/user/mcp-tools.md) and
  [Common workflows](../doc/user/workflows.md)

## Inventory

- [`collections/jira_mcp.json`](collections/jira_mcp.json) — **End users.**
  Curated Jira Cloud MCP collection (12 REST tools: search, issue CRUD,
  transitions, worklog, fields, boards, sprints).
- [`environments/jira_cloud.json`](environments/jira_cloud.json) — **End users.**
  Companion environment: `jira_base_url`, hidden `jira_credentials`,
  `enable_mcp: true`.
- [`collections/mcp.json`](collections/mcp.json) — **Contributors / local
  probing.** Local MCP/SSE probe against PyPost ports (`127.0.0.1:1080` /
  `9080`); used by test helpers. Not the primary “learn Jira + MCP” starter.

## Recommended import order (Jira Cloud pair)

1. **Import the environment** — **Manage Environments → Import…** and choose
   `examples/environments/jira_cloud.json`.
2. **Replace placeholders locally** (do not commit real secrets):
   - `jira_base_url` — your site, for example
     `https://your-company.atlassian.net`
   - `jira_credentials` — `email:api_token` (Atlassian account email and an
     API token from Atlassian account settings); keep the key **Hidden**
3. **Import the collection** — **Import Collection…** and choose
   `examples/collections/jira_mcp.json`.
4. **Select** the **Jira Cloud MCP** environment in the top dropdown.
5. **Send** a request manually, or use an agent while MCP is enabled on that
   environment (already `enable_mcp: true` in the example).

Auth in the collection matches Atlassian Cloud basic auth for REST APIs:
`Authorization: Basic {{ base64(jira_credentials) }}`.

## Secret handling

- Committed fixtures contain **placeholders only** (sample site URL and
  `you@example.com:your-api-token`). Never put real API tokens or passwords in
  git.
- After import, substitute your own values in PyPost (or in a private copy of the
  JSON). Keep credential keys in `hidden_keys`.
- Local runtime data under `collections/` and `environments.json` stays
  gitignored; only the tracked files under
  `examples/{collections,environments}/` are source-controlled fixtures.

## Role of `mcp.json`

Use `collections/mcp.json` when you are developing or probing PyPost’s own
MCP/SSE endpoints locally. For a ready-to-adapt Jira Cloud + MCP workflow, use
the `jira_mcp.json` + `jira_cloud.json` pair instead.
