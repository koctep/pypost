# PYPOST-496: Requirements

## Business goal

Improve maintainability of the Manage Environments dialog by separating concerns that grew
into a single large class.

## User stories

- As a developer, I want environment list UI logic isolated from variable-table logic so each
  area can evolve independently.
- As a user, I expect no change in behavior: add/rename/copy/delete environments, edit
  variables, toggle hidden flags, reorder/delete variables, and MCP toggle must work as before.

## Acceptance criteria

1. `EnvironmentDialog` composes dedicated widgets for the left (environment list) and right
   (variables + MCP) panes.
2. Existing Qt-level tests for `EnvironmentDialog` pass without behavioral regressions.
3. Public test-facing attributes (`env_list`, `vars_table`, `mcp_check`) and helper methods
   used by tests remain available on `EnvironmentDialog`.
4. Logging events for environment and variable actions are unchanged.

## Out of scope

- Moving domain validation out of the UI layer ([PYPOST-497](https://pypost.atlassian.net/browse/PYPOST-497)).
- Changing presenter persistence or dialog entry points.
