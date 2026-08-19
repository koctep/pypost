# Jira MCP Example Project Default (PYPOST-1032)

## Overview

The importable Jira Cloud MCP example pair provides a **soft** preferred project
for normal work. It reduces ambiguity for agents in Jira accounts that contain
multiple projects, but it does not add a PyPost access-control feature.

The implementation is fixture-only. It changes neither the PyPost runtime nor
the external Atlassian MCP server; Jira Cloud remains responsible for
authentication and authorization.

## Architecture

The feature is split between the companion environment, curated request
collection, and their offline import contract:

| Component | Responsibility |
| --- | --- |
| `examples/environments/jira_cloud.json` | Exposes the visible, non-secret `jira_project_key` placeholder beside the hidden credentials. |
| `examples/collections/jira_mcp.json` | Renders `jira_project_key` in the Jira Software board-list `projectKeyOrId` parameter (omitted when unset) and gives agents precise default-project guidance for search and create payloads. |
| Endpoint environment + `MCPServerImpl` | A registry endpoint resolves `{{ jira_project_key }}` from its configured environment snapshot at tool-call time; when unset or empty, `HTTPClient` omits `projectKeyOrId` to grant unconstrained access across all accessible projects (PYPOST-1068). |
| `tests/test_example_fixtures.py` | Loads both JSON files through native importers and locks the placeholder, template binding, guidance, and security wording. |

`jira-list-boards` is the one existing list request whose REST endpoint accepts
the selected project directly. When `jira_project_key` is configured, it is project-scoped;
when `jira_project_key` is omitted or empty, `HTTPClient` omits the `projectKeyOrId`
query parameter so all accessible boards are listed. Its page size and offset are agent inputs
(`maxResults`, `startAt`; PYPOST-1029). Board-sprint and sprint-issue calls
retain their native selected-board or selected-sprint scope; they must not be
described as automatically project-scoped, but they share the same optional,
safely-defaulted pagination pair (PYPOST-1054).

## Usage

After importing the Jira environment, select **Jira Cloud MCP** in the top bar
for GUI sends and replace `jira_project_key` with the normal Jira project key
or ID (or leave it unset/empty for unconstrained multi-project access). For MCP,
create an **MCP Servers…** row that selects the Jira collection and Jira Cloud MCP
environment. That endpoint uses the selected value directly for `jira-list-boards`
(omitting `projectKeyOrId` when unset); changing the top-bar selection does not retarget it.

For `jira-search-issues-jql` and `jira-create-issue`, callers supply a
serialized Jira JSON payload. When `jira_project_key` is configured with a single key
(e.g., `PROJ1`) or multiple comma-separated keys (e.g., `PROJ1, PROJ2`), the collection's
`mcp_description` and `mcp_params` instruct agents to use `project = PROJ1` (single) or
`project in (PROJ1, PROJ2)` (multiple) for normal searches, and to specify the target
project or use the primary project for issue creation. When unset, callers operate across
all accessible projects or specify the project explicitly per operation. PyPost
deliberately does not parse, inject, validate, or override the payload's project field.
A caller can deliberately name another project.

For the import steps and end-user-facing safety notes, see
[`examples/README.md`](../../examples/README.md).

## Configuration

| Key | Committed example value | Handling |
| --- | --- | --- |
| `jira_base_url` | `https://your-team.atlassian.net` | Replace locally with the Jira Cloud site URL. |
| `jira_project_key` | `YOUR_PROJECT_KEY` | Replace locally with a project key, ID, or comma-separated project list (e.g., `PROJ1, PROJ2`). It is visible and must not be in `hidden_keys`. |
| `jira_credentials` | `you@example.com:your-api-token` | Replace locally and keep it as the only hidden key. Never commit a real value. |

The project key is a normal environment variable. Editing the environment
refreshes endpoint snapshots that selected it; changing the top-bar environment
does not alter MCP calls. It is not exposed as an `mcp.request.*` argument.

## Numeric board and sprint identifiers (PYPOST-1038)

The six Jira board/sprint path arguments below accept either a native JSON
integer such as `42` or a decimal JSON string such as `"42"`. Their collection
parameter type is `integer_or_string`, which publishes an integer-or-decimal-
string JSON Schema union to MCP clients. This preserves native-number clients
while supporting the common agent/client string representation.

| Request id | Argument |
| --- | --- |
| `jira-list-board-sprints` | `board_id` |
| `jira-get-sprint` | `sprint_id` |
| `jira-update-sprint` | `sprint_id` |
| `jira-delete-sprint` | `sprint_id` |
| `jira-add-issues-to-sprint` | `sprint_id` |
| `jira-get-sprint-issues` | `sprint_id` |

The request templates validate these values with `to_int` immediately before
building the Jira path. Non-decimal strings, floats, and booleans are invalid;
the request fails before any outbound HTTP dispatch. This input tolerance
changes neither the selected project behavior above nor Jira authorization.

## List pagination (PYPOST-1029 / PYPOST-1054)

These curated list tools declare agent-facing `maxResults` and `startAt`
(`integer_or_string`, rendered with `to_int` into the Agile query string):

| Request id | Notes |
| --- | --- |
| `jira-list-boards` | Still project-scoped via env `jira_project_key`; no longer on the empty-`mcp_params` allowlist |
| `jira-list-board-sprints` | Alongside required `board_id` and `state` |
| `jira-get-sprint-issues` | Alongside required `sprint_id` |

As of PYPOST-1054, both parameters are `required: false` and declare a safe `default`
(`maxResults: 50`, `startAt: 0`), published in the `list_tools` JSON Schema. Omitting either
argument — or passing it explicitly as `null` — no longer fails template render; PyPost fills
it from the declared default before executing the request. Passing an explicit non-`null`
value (native integer or decimal string, e.g. `25`/`"25"`) still overrides the default.
Before PYPOST-1054 both parameters were `required: true` with no template fallback, so
omitting them failed closed at render time — see
[MCP Integration § Optional MCP parameter defaults](mcp_integration.md#optional-mcp-parameter-defaults-pypost-1054)
for the full model/schema/execution/observability details.

## Security boundary

`jira_project_key` is guidance, not an authorization, permission, or security
boundary. It cannot prevent an authorized caller from accessing another
project, and it must not be used as a substitute for Jira permission schemes,
dedicated accounts, or external MCP-server configuration. Jira Cloud decides
whether a deliberately requested cross-project operation is permitted.

## Testing and troubleshooting

Run the fixture contract without Jira credentials, a running MCP listener, or
network access:

```bash
make test PYTEST_ARGS='tests/test_example_fixtures.py -v'
```

That module also locks companion-env coverage, Basic auth convention,
`mcp.request.*` ↔ `mcp_params`, and the fixed-input allowlist (PYPOST-1028).
See
[Env / auth / MCP params contracts](testing.md#env--auth--mcp-params-contracts-pypost-1028).

| Symptom | Check |
| --- | --- |
| Board listing ignores the expected project | Ensure the endpoint selected Jira Cloud MCP as its environment and `jira_project_key` is set; confirm the request retains `projectKeyOrId: {{ jira_project_key }}`. |
| An agent creates or searches in the wrong project | Inspect the supplied serialized payload. The project key is guidance only; the payload remains caller controlled. |
| Board or sprint follow-up results are broader than expected | These endpoints follow the explicitly selected board or sprint. Do not claim that the project default filters them. |
| Project key is hidden or importer tests fail | Keep only `jira_credentials` in `hidden_keys` and use the obvious placeholder in the committed fixture. |
| Cross-project work is rejected or allowed unexpectedly | Diagnose Jira Cloud permissions and the target project; this example default does not grant or revoke access. |
| A board or sprint call rejects its identifier | Supply `42` or `"42"`; do not supply a boolean, float, whitespace-padded value, exponent notation, or a nonnumeric string. |
| Env/auth/`mcp_params` fail | Fix companion key, auth, or `mcp_params`; empty only on allowlist. |
| List boards/sprints/issues omit page size | No action needed — `maxResults`/`startAt` are optional and default to `50`/`0` (PYPOST-1054). Pass explicit values (e.g. `25`/`100`) only to override the default page or offset. |
