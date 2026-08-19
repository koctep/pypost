# Requirements: PYPOST-1091

## Summary

1. Expose `maxResults` and `startAt` pagination query parameters on `jira-search-assignable-users` in `examples/collections/jira_mcp.json` with the same optional-with-safe-default pattern established in PYPOST-1054 (`maxResults`: default 50, `startAt`: default 0, type `integer_or_string`).
2. Add explicit pagination guidance to `jira-search-issues-jql`'s `mcp_description` and `search_payload.description` indicating that `search_payload` supports pagination fields such as `maxResults` and `nextPageToken` (or `startAt`).

## Background & Motivation

Follow-up TD-3 from PYPOST-1054:
- In `examples/collections/jira_mcp.json`, `jira-list-boards`, `jira-list-board-sprints`, and `jira-get-sprint-issues` declare optional pagination parameters (`maxResults` and `startAt`) with defaults (50, 0).
- `jira-search-assignable-users` (`GET /rest/api/3/user/assignable/search`) also supports `maxResults` and `startAt` in Jira Cloud's REST API, but omitted them from its `params` and `mcp_params`.
- `jira-search-issues-jql` uses a JSON body `search_payload` for `POST /rest/api/3/search/jql`. Because the body is a serialized string, structural default injection is not possible, but agents need pagination guidance in the description.

## Detailed Requirements

1. **`jira-search-assignable-users` in `examples/collections/jira_mcp.json`**:
   - In `params`: add `"maxResults": "{{ to_int(mcp.request.maxResults) }}"` and `"startAt": "{{ to_int(mcp.request.startAt) }}"`.
   - In `mcp_params`: declare `maxResults` (`type: "integer_or_string"`, `required: false`, `default: 50`) and `startAt` (`type: "integer_or_string"`, `required: false`, `default: 0`).
   - In `tests/test_example_fixtures.py`: include `"jira-search-assignable-users"` in `PAGINATED_JIRA_MCP_LIST_REQUEST_IDS`.

2. **`jira-search-issues-jql` guidance**:
   - Update `mcp_description` and `search_payload.description` to mention pagination fields in `search_payload`.

3. **Verification**:
   - `test_jira_mcp_list_requests_expose_pagination_mcp_params` must pass for all 4 paginated list tools.
   - `make lint` and fixture tests must pass.
