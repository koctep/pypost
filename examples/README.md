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
  Curated Jira Cloud MCP collection (22 REST tools): issue search/CRUD,
  transitions, worklog, fields, comments, assign, epic/parent link, boards,
  sprints (list/create/update/delete/membership), backlog, and
  assignable-user search.
- [`environments/jira_cloud.json`](environments/jira_cloud.json) — **End users.**
  Companion environment: `jira_base_url`, visible `jira_project_key`, hidden `jira_credentials`,
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
   - `jira_project_key` — set this to the Jira project key or ID that should
     guide normal issue search, issue creation, and board discovery
   - `jira_credentials` — `email:api_token` (Atlassian account email and an
     API token from Atlassian account settings); keep the key **Hidden**
3. **Import the collection** — **Import Collection…** and choose
   `examples/collections/jira_mcp.json`.
4. **Select** the **Jira Cloud MCP** environment in the top dropdown.
5. **Send** a request manually, or use an agent while MCP is enabled on that
   environment (already `enable_mcp: true` in the example).

Auth in the collection matches Atlassian Cloud basic auth for REST APIs:
`Authorization: Basic {{ base64(jira_credentials) }}`.

`jira_project_key` is a soft default for normal work. It is not an authorization
and not a security boundary or permission control. A user may deliberately work
in a different project when their Jira permissions allow it. Board discovery uses
the project-aware Jira parameter; board and sprint follow-up tools keep the
scope of the selected board or sprint rather than simulating a project lock.

## Coverage vs gaps

This collection is a **practical analog** of the Atlassian MCP Jira surface
used by in-repo agent skills and workflows — not a full dump of every Jira
Cloud or Atlassian MCP tool.

**Included (MCP-exposed requests):**

| Area | Request ids |
| ---- | ----------- |
| Search / fields | `jira-search-issues-jql`, `jira-search-fields` |
| Issue lifecycle | `jira-get-issue`, `jira-create-issue`, `jira-update-issue` |
| Workflow | `jira-get-transitions`, `jira-transition-issue` |
| Comments / assign | `jira-add-comment`, `jira-assign-issue` |
| Assignable users | `jira-search-assignable-users` |
| Worklog | `jira-add-worklog`, `jira-get-worklog` |
| Epic / parent | `jira-link-issue-parent` (uses `fields.parent`) |
| Boards / sprint read | `jira-list-boards`, `jira-list-board-sprints`, `jira-get-sprint` |
| Sprint write | `jira-create-sprint`, `jira-update-sprint`, `jira-delete-sprint` |
| Sprint issues | `jira-get-sprint-issues` |
| Sprint membership | `jira-add-issues-to-sprint`, `jira-move-issues-to-backlog` |

`jira-move-issues-to-backlog` is the supported remove-from-sprint path.

**Explicit gaps** (out of scope unless added later):

- Service Desk / JSM (queues, request types, customer requests)
- ProForma forms and answers
- Watchers, attachments/images, delete issue
- Remote/issue-link CRUD beyond epic-parent linking
- Versions/components batch APIs, SLA, development info
- Cross-project dependencies and customer-facing comment flags
- `jira_batch_create_issues` (skills deliberately avoid batch create)

External Atlassian MCP may remain configured for agents; these fixtures do not
replace that server — they ship a PyPost-native analog for the in-scope set.

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
