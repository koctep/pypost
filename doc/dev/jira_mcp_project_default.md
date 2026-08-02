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
| `examples/collections/jira_mcp.json` | Renders `jira_project_key` in the Jira Software board-list `projectKeyOrId` parameter and gives agents precise default-project guidance for search and create payloads. |
| Active environment + `MCPServerImpl` | Existing code resolves `{{ jira_project_key }}` at tool-call time with other environment values; it does not inspect or merge JSON payload fields. |
| `tests/test_example_fixtures.py` | Loads both JSON files through native importers and locks the placeholder, template binding, guidance, and security wording. |

`jira-list-boards` is the one existing list request whose REST endpoint accepts
the selected project directly. Board-sprint and sprint-issue calls retain their
native selected-board or selected-sprint scope; they must not be described as
automatically project-scoped.

## Usage

After importing the Jira environment, select **Jira Cloud MCP** as the active
environment and replace `jira_project_key` with the normal Jira project key or
ID. The selected value is used directly by `jira-list-boards` on the next GUI
send or MCP tool call.

For `jira-search-issues-jql` and `jira-create-issue`, callers supply a
serialized Jira JSON payload. The collection's `mcp_description` and
`mcp_params` instruct agents to use `jira_project_key` as the normal project in
that payload; PyPost deliberately does not parse, inject, validate, or override
the payload's project field. A caller can deliberately name another project.

For the import steps and end-user-facing safety notes, see
[`examples/README.md`](../../examples/README.md).

## Configuration

| Key | Committed example value | Handling |
| --- | --- | --- |
| `jira_base_url` | `https://your-team.atlassian.net` | Replace locally with the Jira Cloud site URL. |
| `jira_project_key` | `YOUR_PROJECT_KEY` | Replace locally with the normal project key or ID. It is visible and must not be in `hidden_keys`. |
| `jira_credentials` | `you@example.com:your-api-token` | Replace locally and keep it as the only hidden key. Never commit a real value. |

The project key is a normal environment variable, so the existing active-
environment behavior applies: a later edit or environment change is used for
subsequent MCP calls. It is not exposed as an `mcp.request.*` argument.

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
.venv/bin/python -m pytest tests/test_example_fixtures.py -v
```

| Symptom | Check |
| --- | --- |
| Board listing ignores the expected project | Ensure the active environment is Jira Cloud MCP and `jira_project_key` is set; confirm the request retains `projectKeyOrId: {{ jira_project_key }}`. |
| An agent creates or searches in the wrong project | Inspect the supplied serialized payload. The project key is guidance only; the payload remains caller controlled. |
| Board or sprint follow-up results are broader than expected | These endpoints follow the explicitly selected board or sprint. Do not claim that the project default filters them. |
| Project key is hidden or importer tests fail | Keep only `jira_credentials` in `hidden_keys` and use the obvious placeholder in the committed fixture. |
| Cross-project work is rejected or allowed unexpectedly | Diagnose Jira Cloud permissions and the target project; this example default does not grant or revoke access. |
| A board or sprint call rejects its identifier | Supply `42` or `"42"`; do not supply a boolean, float, whitespace-padded value, exponent notation, or a nonnumeric string. |
