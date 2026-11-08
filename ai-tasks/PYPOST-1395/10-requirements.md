# PYPOST-1395: [PYPOST-1312] Add sample hidden_response_fields to remaining example collections

## Goals

When developers and automated systems interact with cloud APIs (such as GitHub, GitLab, Jira Cloud, and Google Drive), API response payloads routinely include confidential authentication tokens, user account identifiers, email addresses, and Personally Identifiable Information (PII). In PyPost, Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) established a unified dual-surface response field masking architecture (`hidden_response_fields`):
1. **Interactive Desktop Presentation**: Sensitive fields in the GUI `ResponseView` are masked by default with an intuitive in-place click-to-reveal mechanism, safeguarding against accidental disclosure during screen sharing, demos, and presentations.
2. **Autonomous AI Agent Safety**: Responses returned to AI agents via Model Context Protocol (MCP) tools are permanently and irreversibly sanitized (`***`), preventing secret leakage into Large Language Model (LLM) contexts or remote logs.

During the initial rollout of this feature in [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380), only the Google Drive collection (`examples/collections/google_drive.json`) was configured with a sample masked request (`gdrive-about-get`). The remaining shipped reference collections—specifically the curated catalog collections for GitHub (`github_mcp.json`), GitLab (`gitlab_mcp.json`), and Jira Cloud (`jira_mcp.json`)—contain requests that return user credentials and PII, but lack sample `hidden_response_fields` configurations.

This task delivers immediate business value by:
- **Demonstrating Best Practices Out of the Box**: Providing users who explore or import PyPost's bundled collections with realistic, turn-key examples of how to configure field-level secret and PII masking for industry-standard APIs.
- **Fail-Safe Defaults for Agent Tool Use**: Ensuring that when AI agents invoke bundled user-identity tools (such as retrieving authenticated GitHub or Jira profiles), private emails and account metadata are protected by default without requiring manual user reconfiguration.
- **Consistency Across Reference Catalog**: Bringing the GitHub, GitLab, and Jira Cloud reference collections into parity with the Google Drive reference implementation.

## Programming Language

- **Implementation language**: Python (for collection fixture validation, automated contract tests, and repository test suites).

## User Stories

- As an **API Developer / Postman User Migrating to PyPost**, I want bundled reference collections (GitHub, GitLab, Jira Cloud) to include pre-configured examples of `hidden_response_fields`, so that I can learn how to protect sensitive response fields without guessing selector syntax or consulting external documentation.
- As an **AI Agent Operator**, I want tools executed from bundled collections that return user profiles or account credentials to have sensible masking configured by default, so that sensitive PII (such as user email addresses, account IDs, or private security settings) is never leaked into prompt history or telemetry logs.
- As a **Security & Compliance Officer**, I want all bundled API collections distributed with PyPost to model least-privilege information disclosure, demonstrating compliance with data privacy standards (GDPR, SOC 2) regarding PII exposure in developer tooling.
- As a **PyPost Maintainer / Contributor**, I want automated contract tests to verify that bundled collection fixtures maintain valid Pydantic schema compliance and preserve configured `hidden_response_fields` under serialization round-trips.

## Definition of Done

This task is considered complete when:

1. **Reference Collection Scope Identified & Validated**:
   - The active bundled reference collections in `examples/collections/` (specifically `github_mcp.json`, `gitlab_mcp.json`, and `jira_mcp.json`) are audited for endpoints returning sensitive secrets, user credentials, or PII.
   - The mention of "Slack, Notion" in the Jira description is formally reconciled (clarifying that PyPost bundles GitHub, GitLab, and Jira Cloud; no Slack or Notion collections currently exist in the repository).

2. **Sample Hidden Fields Configured on Representative Requests**:
   - For each targeted bundled collection, at least one high-value request returning user identity or account secrets is configured with `hidden_response_fields`:
     - **GitHub Collection (`examples/collections/github_mcp.json`)**: Configure a user-identity endpoint (e.g. `github-get-authenticated-user`) with selectors targeting sensitive PII and account fields (e.g., `email`, `two_factor_authentication`, `plan.name`).
     - **GitLab Collection (`examples/collections/gitlab_mcp.json`)**: Configure a user-identity endpoint (e.g. `gitlab-get-current-user`) with selectors targeting sensitive PII (e.g., `email`, `commit_email`, `public_email`).
     - **Jira Cloud Collection (`examples/collections/jira_mcp.json`)**: Configure a user-identity endpoint (e.g. `jira-get-current-user`) with selectors targeting sensitive PII (e.g., `emailAddress`, `accountId`).

3. **Realistic Selector Patterns Demonstrated**:
   - Configurations demonstrate both direct/simple key matching (e.g., `email`, `emailAddress`) and dot-notation path matching (e.g., `plan.name`), reflecting best practices outlined in `doc/dev/hidden_response_fields.md`.

4. **Schema & Serialization Compatibility**:
   - All modified collection files strictly validate against PyPost's `Collection` Pydantic model (`version: "2.0.0"`).
   - Round-trip serialization (`read_collection_file` -> `model_dump_json`) preserves `hidden_response_fields` with exact fidelity.

5. **Automated Verification & Zero Regressions**:
   - Automated tests (such as contract tests in `tests/test_example_fixtures.py`, `tests/test_github_mcp_collection.py`, `tests/test_gitlab_mcp_collection.py`, or dedicated edge-case verification tests) assert the presence and correct configuration of `hidden_response_fields` across the updated collections.
   - All existing offline collection tests and quality gates (`make check`, `make lint`, `make typecheck`, `make test`) pass with zero errors.

## Task Description

### Problem Statement

In Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312), PyPost added support for request-level `hidden_response_fields`. This mechanism allows requests to specify JSON keys or paths that must be masked in desktop GUI response views (reversible via click-to-reveal) and permanently redacted in MCP tool invocations.

While the feature implementation and core contracts were established in [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) through [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380), only the Google Drive collection (`google_drive.json`) was updated to showcase this functionality via request `gdrive-about-get`. The remaining reference collections bundled with the application—GitHub (`github_mcp.json`), GitLab (`gitlab_mcp.json`), and Jira Cloud (`jira_mcp.json`)—have empty or omitted `hidden_response_fields`. Consequently:
- New users importing GitHub, GitLab, or Jira collections do not see examples of response masking.
- AI agents executing MCP tools generated from these reference collections receive plain-text PII (e.g., user email addresses, private account flags).

Debt task [PYPOST-1395](https://pypost.atlassian.net/browse/PYPOST-1395) resolves this gap by expanding sample `hidden_response_fields` across the remaining bundled reference collections.

### Scope

- **In Scope**:
  - Updating curated reference collections in `examples/collections/`:
    - `examples/collections/github_mcp.json`
    - `examples/collections/gitlab_mcp.json`
    - `examples/collections/jira_mcp.json`
  - Selecting authentic user-profile or credential requests in each collection and populating their `hidden_response_fields` with realistic, non-disruptive selectors.
  - Adding automated contract assertions to verify that each target collection includes the configured `hidden_response_fields`.
  - Ensuring companion catalogs or test stubs remain in sync and passing.

- **Out of Scope**:
  - Inventing or authoring new third-party service collections (such as Slack or Notion) that are not currently part of the PyPost codebase.
  - Altering the core JSON masking engine, `McpResponseSanitizer`, `JsonSelectorEngine`, or `ResponseMaskController` algorithms.
  - Modifying the Pydantic data models or serialization formats.

### Constraints and Assumptions

- **Non-Breaking Changes**: Adding `hidden_response_fields` to collection JSON files is fully backward-compatible, as `RequestData.hidden_response_fields` defaults to an empty list `[]`.
- **Display & Serialization Only**: Masking affects only presentation in the GUI and serialization in MCP responses; underlying `ResponseData` in-memory structures remain pristine.
- **Offline / Loopback Testing**: All repository tests must operate entirely offline without live network dependencies, relying on existing loopback stubs and fixture readers.
- **Make-Only Invocation**: All verification commands must follow `AGENTS.md` and use `make` targets.

### Business Entities & Relationships

```
+-------------------------------------------------------+
|                 Bundled Collection                     |
|  - id, name, description, version ("2.0.0")           |
|  - examples/collections/{github_mcp, gitlab_mcp, ...} |
+-------------------------------------------------------+
                           |
                           | 1..* contains
                           v
+-------------------------------------------------------+
|                 Reference Request                     |
|  - id: "github-get-authenticated-user", etc.          |
|  - method, url, headers, params, body                 |
|  - expose_as_mcp: bool                                |
+-------------------------------------------------------+
                           |
                           | 0..* configures
                           v
+-------------------------------------------------------+
|            Hidden Response Field Selector             |
|  - Direct key: "email", "emailAddress"                |
|  - Dot-notation: "plan.name", "user.emailAddress"     |
+-------------------------------------------------------+
```

### Use Scenarios

- **Scenario 1: Developer Demonstrates PyPost via GitHub MCP**:
  A developer connects PyPost to GitHub and invokes the `github-get-authenticated-user` tool while sharing their screen on a video call. Because `email` and `two_factor_authentication` are configured in `hidden_response_fields`, the GUI displays them with masked underlines (`***`). The developer can click to reveal their own email if necessary, while preventing unintended audience exposure.
- **Scenario 2: Autonomous Coding Agent Inspects Jira Current User**:
  An AI agent invokes the `jira-get-current-user` tool through the MCP protocol. The MCP server sanitizes the response, permanently redacting `emailAddress` and `accountId` as `***`. The agent receives the user's display name and operational metadata without ingesting personal email addresses into context tokens.
- **Scenario 3: CI/CD Pipeline Verifies Bundled Collections**:
  PyPost's automated test suite runs during pull request evaluation. Contract tests load each bundled JSON collection and assert that the required requests exist, parse cleanly into Pydantic models, and contain the expected `hidden_response_fields`.

## Q&A

- **Q1: The Jira issue mentions "(e.g. GitHub, Slack, Notion, Jira)". Do we need to create Slack and Notion collections?**
  **A**: No. The parenthetical in the Jira description is an illustrative example of common cloud services. In the PyPost repository, the curated bundled collections cataloged in `examples/builtin-collections.yaml` are GitHub (`github_mcp.json`), GitLab (`gitlab_mcp.json`), and Jira Cloud (`jira_mcp.json`), alongside `google_drive.json` (which already has masking sample configured). PyPost does not ship Slack or Notion collections. The scope of PYPOST-1395 is to expand masking to the actual remaining bundled collections in the repository.

- **Q2: Which specific requests should be updated in each collection?**
  **A**:
  1. `github_mcp.json`: `github-get-authenticated-user` (`GET /user`). Returns user profile details containing sensitive PII (`email`, `two_factor_authentication`, `plan.name`).
  2. `gitlab_mcp.json`: `gitlab-get-current-user` (`GET /user`). Returns user profile details containing sensitive PII (`email`, `commit_email`, `public_email`).
  3. `jira_mcp.json`: `jira-get-current-user` (`GET /rest/api/3/myself`). Returns Atlassian account details containing PII (`emailAddress`, `accountId`).

- **Q3: Will adding `hidden_response_fields` break existing tests for GitHub, GitLab, or Jira MCP collections?**
  **A**: No. In MCP integration and unit tests, loopback stubs test tool arguments and responses. Since `hidden_response_fields` only redacts specified fields in the MCP string output and GUI view, any tests asserting the exact unmasked response text of these specific tools will simply reflect the masked fields (or can verify the masking behavior directly, enhancing test coverage). All existing collection validation tests will be run and confirmed passing.

- **Q4: How should selector naming be chosen?**
  **A**: Selectors should follow the proven pattern established in `google_drive.json` (`gdrive-about-get`): targeting direct PII properties (`email`, `emailAddress`, `commit_email`) as well as nested structures (e.g. `plan.name`), demonstrating both simple keys and dot-notation paths supported by `JsonSelectorEngine`.
