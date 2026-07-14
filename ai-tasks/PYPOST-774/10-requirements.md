# PYPOST-774 — Requirements

> Parent: [PYPOST-690](https://pypost.atlassian.net/browse/PYPOST-690) audit R-P3-002

## Problem

`doc/mcp_integration.md` (user-facing setup) and `doc/dev/mcp_integration.md` (developer
reference) do not reference each other at the top level. Operators and maintainers must search
both files to connect setup steps with architecture and implementation details.

## Acceptance Criteria

1. `doc/mcp_integration.md` has a See also section linking to the developer guide.
2. `doc/dev/mcp_integration.md` has a See also section linking to the user guide.
3. No application code changes.
4. `make check` passes.

## Out of Scope

- Moving either guide under `doc/dev/`
- Other MCP doc cross-links (secrets policy, trust model — separate tickets)
- Updating inline cross-links already present in body sections
