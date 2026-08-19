# PYPOST-1055: Migrate jira-mcp Agile list pagination from startAt to nextPageToken

## Programming Language

Python is the implementation language for the application runtime, collection tooling, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

Follow-up from PYPOST-1029 (TD-2). In Jira REST APIs, Atlassian has different pagination mechanisms across the product surface:
1. Classic Agile REST API (`/rest/agile/1.0/board`, `/rest/agile/1.0/board/{boardId}/sprint`, `/rest/agile/1.0/sprint/{sprintId}/issue`) uses offset-based pagination (`startAt` and `maxResults`).
2. Modern Jira Cloud Platform API (`/rest/api/3/search/jql`) uses token-based cursor pagination (`nextPageToken` and `maxResults`).

**Business goal:** Evaluate and document the exact pagination contracts for Jira MCP tooling. Establish clear guidance and contract verification ensuring that:
- Curated Agile endpoints (`jira-list-boards`, `jira-list-board-sprints`, `jira-get-sprint-issues`) maintain their compliant, optional `startAt` / `maxResults` pagination with safe defaults (from PYPOST-1054).
- Issue searching via `jira-search-issues-jql` provides token-based pagination with `nextPageToken` in its search payload.
- Agent paging loops for both paradigms are documented, tested, and contractually protected.

## User Stories

- As an **AI agent querying Jira issues**, I want to use `jira-search-issues-jql` with `nextPageToken` so that I can reliably paginate through large issue result sets without index drift.
- As an **AI agent querying boards and sprints**, I want `jira-list-boards` and `jira-list-board-sprints` to continue accepting optional `startAt` and `maxResults` with standard defaults (50 and 0), so that calls remain compatible with Atlassian's Agile API.
- As an **API collection maintainer**, I want clear documentation and tests locking the pagination requirements across all Jira MCP tools, preventing regressions.

## Definition of Done

- [ ] Technical evaluation of Atlassian REST API pagination requirements is documented in requirements and architecture artifacts.
- [ ] Agile list endpoints (`jira-list-boards`, `jira-list-board-sprints`, `jira-get-sprint-issues`) retain optional `maxResults` and `startAt` with defaults `50` and `0`.
- [ ] Issue search endpoint `jira-search-issues-jql` is verified to support `nextPageToken` in `search_payload`.
- [ ] Offline fixture and contract tests in `tests/test_example_fixtures.py` and `tests/test_pypost_1077_verification_artifacts.py` pass 100% green.
- [ ] Developer documentation in `doc/dev/jira_mcp_project_default.md` and `doc/dev/mcp_integration.md` is updated.

## Scope

**In Scope:**
- Architectural evaluation of offset (`startAt`) vs token (`nextPageToken`) pagination in Atlassian Jira APIs.
- Locking of tool schemas, defaults, and contracts for Jira MCP list tools.
- Documentation of agent pagination loops for both Agile tools and JQL search.
- Verification of test suites and static AST contract checkers.

**Out of Scope:**
- Breaking changes to Agile REST endpoints that would cause 400 Bad Request against Jira Cloud Agile APIs.
- Live Jira network credentials in CI.

## Q&A

**Q: Does Jira Cloud Agile API (`/rest/agile/1.0/...`) support `nextPageToken` query parameters?**
**A:** No. Atlassian's Jira Agile REST API v1.0 specifications for board and sprint listings require `startAt` and `maxResults`. Attempting to pass `nextPageToken` as an Agile query param is rejected or ignored by Jira Cloud.

**Q: Where is `nextPageToken` supported in Jira Cloud?**
**A:** In the Jira Cloud Platform REST API v3 Enhanced JQL Search (`/rest/api/3/search/jql`), which is exposed in PyPost via `jira-search-issues-jql`.
