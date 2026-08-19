# Observability: PYPOST-1091

## Overview

Audited observability implications of adding pagination parameters to `jira-search-assignable-users`.

## Findings

- Tool calls omitting `maxResults` or `startAt` will trigger `mcp_param_default_applied` INFO logs and increment `mcp_param_defaults_applied_total{method="GET"}` counter according to PYPOST-1054's defaulting engine.
- Tool input schema correctly reflects defaults `50` and `0` for `maxResults` and `startAt`.
