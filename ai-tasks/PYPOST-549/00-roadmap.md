# Roadmap: PYPOST-549

Programming language: Python (.cursor/lsr/do-python.md) — implementation lives in child stories.

Epic type: **vision / coordination** — no direct code changes; child stories PYPOST-550..557
(and related PYPOST-561, PYPOST-562) deliver features.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified README.md Vision section against Jira epic — aligned; no edit required
  - [x] No epic-level code changes (implementation tracked in child stories)
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-549/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-549/20-architecture.md`

### STEP 3: Development

- README.md (verified; unchanged)
- Child story implementation: see PYPOST-550, PYPOST-551, PYPOST-552..557

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-549/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-549/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-549/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-549/70-dev-docs.md`
- Cross-ref: `doc/dev/mcp_integration.md`, `doc/dev/testing.md`

## Child story progress

| Key | Summary | Status |
| --- | --- | --- |
| [PYPOST-550](https://pypost.atlassian.net/browse/PYPOST-550) | Env vars in MCP tool execution | Done |
| [PYPOST-551](https://pypost.atlassian.net/browse/PYPOST-551) | Streamable HTTP transport | Done |
| [PYPOST-552](https://pypost.atlassian.net/browse/PYPOST-552) | E2E verify with Cursor | To Do |
| [PYPOST-553](https://pypost.atlassian.net/browse/PYPOST-553) | Tool metadata authoring | To Do |
| [PYPOST-554](https://pypost.atlassian.net/browse/PYPOST-554) | Secrets / hidden vars policy | To Do |
| [PYPOST-555](https://pypost.atlassian.net/browse/PYPOST-555) | UI preview of tool contract | To Do |
| [PYPOST-556](https://pypost.atlassian.net/browse/PYPOST-556) | MCP tools overview + server status | To Do |
| [PYPOST-557](https://pypost.atlassian.net/browse/PYPOST-557) | Structured tool call result | To Do |
| [PYPOST-561](https://pypost.atlassian.net/browse/PYPOST-561) | Prometheus in user-facing docs | To Do |
| [PYPOST-562](https://pypost.atlassian.net/browse/PYPOST-562) | Extended MCP Prometheus metrics | To Do |

## Worklog

role: execution, step: 7, tokens_used: (orchestrator aggregate)
