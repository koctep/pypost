# Architecture: PYPOST-1091

## Design Specifications

### 1. `jira-search-assignable-users` Schema and Params

```json
{
  "id": "jira-search-assignable-users",
  "name": "Jira Search Assignable Users",
  "method": "GET",
  "url": "{{ jira_base_url }}/rest/api/3/user/assignable/search",
  "headers": {
    "Accept": "application/json",
    "Authorization": "Basic {{ base64(jira_credentials) }}"
  },
  "params": {
    "query": "{{ mcp.request.query }}",
    "issueKey": "{{ mcp.request.issue_key }}",
    "maxResults": "{{ to_int(mcp.request.maxResults) }}",
    "startAt": "{{ to_int(mcp.request.startAt) }}"
  },
  "body": "",
  "body_type": "json",
  "yaml_as_json": false,
  "post_script": "",
  "expose_as_mcp": true,
  "mcp_description": "Search users assignable to a Jira issue; use accountId from results with jira-assign-issue.",
  "mcp_params": {
    "query": {
      "type": "string",
      "description": "Text to match display name or email.",
      "required": true
    },
    "issue_key": {
      "type": "string",
      "description": "Issue key that scopes assignable-user search.",
      "required": true
    },
    "maxResults": {
      "type": "integer_or_string",
      "description": "Maximum users per page (maxResults). Defaults to 50 when omitted. Accepted as a native integer or decimal string.",
      "required": false,
      "default": 50
    },
    "startAt": {
      "type": "integer_or_string",
      "description": "0-based offset into the user list (startAt). Defaults to 0 when omitted. Accepted as a native integer or decimal string.",
      "required": false,
      "default": 0
    }
  },
  "retry_policy": null
}
```

### 2. `jira-search-issues-jql` Description Guidance

Update `mcp_description`:
"Search Jira issues with JQL. If this endpoint's selected environment defines jira_project_key, start normal searches with project = <key> (for a single project) or project in (<key1>, <key2>, ...) (for multiple comma-separated projects); when unset, search across all accessible projects. Use another permitted project only when explicitly requested. search_payload must be a JSON object accepted by POST /rest/api/3/search/jql (may include fields such as jql, maxResults, nextPageToken, fields)."

### 3. Contract Tests

In `tests/test_example_fixtures.py`:
Add `"jira-search-assignable-users"` to `PAGINATED_JIRA_MCP_LIST_REQUEST_IDS`.
