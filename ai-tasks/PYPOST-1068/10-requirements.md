# PYPOST-1068: Jira MCP: Unconstrained Access When jira_project_key Is Unset

## Goals

When using the PyPost Jira MCP integration, users and autonomous agents may need to work across multiple Jira projects or operate in Jira instances where no single project should be prioritized. Previously, the integration assumed a single preferred project key was always present. When that key was omitted, board listing and search discovery failed or returned unintended empty results due to accidental empty-filter restrictions.

This task aims to:
1. Provide unconstrained, cross-project access for board listing and issue search when no default project key is configured in the environment.
2. Preserve project-scoped filtering and guidance when a default project key is explicitly configured in the environment.
3. Ensure agents receive accurate guidance on how to formulate queries in both single-project and multi-project operating modes.

## User Stories

- **As a Developer/Agent working across multiple Jira projects**, I want to omit the project key from my environment configuration so that board listing and issue searches discover all projects and boards accessible under my credentials without artificial filtering.
- **As a Developer/Agent dedicated to a single Jira project**, I want to set a default project key in my environment so that routine board listing and search actions conveniently default to my primary project.
- **As an AI Agent using the Jira MCP tools**, I want clear instructions in tool descriptions explaining how project scoping operates in both configured and unconfigured modes.

## Definition of Done

1. **Unconstrained Mode (when project key is unset or empty)**:
   - Requesting the list of boards returns all boards across all accessible projects without applying empty-value query restrictions.
   - Searching issues and creating issues guide callers to operate across all permitted projects or specify the target project per operation.
2. **Project-Scoped Mode (when project key is set)**:
   - Requesting the list of boards scopes results to the configured project.
   - Tool guidance instructs callers to use the configured project as the routine default while permitting explicit overrides when requested.
3. **Compatibility & Reliability**:
   - Existing workflows and single-project configurations continue to function without behavioral regressions.
   - Both modes are verifiable and documented with clear developer instructions.

## Task Description

- **Problem**: When a user or agent does not define a default Jira project key in their environment configuration, the integration passes an empty value filter instead of omitting the filter, preventing full discovery of accessible Jira boards and confusing query guidance.
- **Business Objective**:
  - Make project scoping strictly optional.
  - When unset: provide unconstrained access to all accessible boards and projects.
  - When set: provide scoped default access to the designated project.
- **Constraints**:
  - Jira credentials and permissions remain the source of truth for authorization.
  - Project configuration remains optional guidance rather than a security boundary.

## Q&A

- **Q: Does unconstrained mode allow accessing projects for which the user lacks permissions?**
  - A: No. Jira server authentication and authorization always govern access.
- **Q: What is the expected default behavior for an agent in unconstrained mode?**
  - A: In unconstrained mode, the agent searches across all accessible projects or specifies the project explicitly when creating issues.
