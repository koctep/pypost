# PYPOST-1069: Jira MCP: Support Multiple Projects in jira_project_key

## Goals

Users and AI agents often manage workflows spanning multiple related Jira projects (e.g. `CORE, UI, INFRA`). Currently, `jira_project_key` configuration supports only a single project key. When users specify multiple projects, tools and agents lack structured guidance on formatting JQL queries across the full list (using `project in (...)`) and handling board discovery across the specified project set.

This task aims to:
1. Support multiple comma-separated project keys in `jira_project_key` (e.g., `"PROJ1, PROJ2, PROJ3"`).
2. Ensure full backward compatibility with single project keys (`"PROJ1"`).
3. Handle whitespace trimming and empty element normalization seamlessly.
4. Provide clear agent guidance:
   - For issue search: guide agents to use `project in (PROJ1, PROJ2)` when multiple keys are configured, or `project = PROJ1` for a single key.
   - For issue creation: guide agents to specify the target project or default to the primary (first) project in the list.
   - For board discovery: guide board discovery across the configured project set.

## User Stories

- **As a Developer/Agent managing multiple related Jira projects**, I want to set `jira_project_key` to a comma-separated list of project keys (e.g., `"FRONTEND, BACKEND"`) so that search and board operations naturally cover my team's full scope.
- **As a Developer/Agent with a single project**, I want my existing single-key configuration (e.g., `"PYPOST"`) to continue working with zero configuration changes.
- **As an AI Agent**, I want unambiguous guidance in tool descriptions showing how to formulate JQL searches (`project in (...)`) and create issues when multiple project keys are specified.

## Definition of Done

1. **Multiple Project Key Format Support**:
   - `jira_project_key` accepts comma-separated values (e.g., `"PROJ1, PROJ2"` or `" PROJ1 , , PROJ2 "`).
   - Whitespace is trimmed and empty tokens are ignored.
2. **Search Guidance**:
   - `jira-search-issues-jql` tool and parameter descriptions explain how to query multiple projects using `project in (...)` when multiple keys are configured.
3. **Creation Guidance**:
   - `jira-create-issue` tool and parameter descriptions explain specifying the target project explicitly or using the primary project from the configured list.
4. **Board Discovery Guidance**:
   - `jira-list-boards` tool description explains project scoping for single and multiple project configurations.
5. **Backward Compatibility**:
   - Single-project key configurations continue working without any behavior change or syntax difference.
6. **Testing and Documentation**:
   - Tests lock the multi-project guidance and comma-separated parsing behavior.
   - Developer documentation in `doc/dev/jira_mcp_project_default.md` and `examples/README.md` documents multi-project configurations.

## Task Description

- **Problem**: When a user specifies multiple projects in `jira_project_key` as a comma-separated string, the tools do not guide agents on using `project in (...)` JQL syntax, and descriptions only mention single-project `project = <key>` syntax.
- **Business Objective**:
  - Enable multi-project team configurations in Jira MCP.
  - Standardize multi-project JQL search guidance (`project in (...)`) and creation rules.
  - Preserve 100% backward compatibility for single-project setups.
- **Constraints**:
  - Jira permissions remain the authorization authority.
  - Project configuration remains soft default guidance.

## Q&A

- **Q: How should an agent format JQL search when `jira_project_key` is `"ALPHA, BETA"`?**
  - A: The agent should construct JQL starting with `project in (ALPHA, BETA)`.
- **Q: How should an agent select a project when creating an issue if multiple projects are configured?**
  - A: The caller should specify the target project explicitly in `fields.project.key` or use the first/primary project.
