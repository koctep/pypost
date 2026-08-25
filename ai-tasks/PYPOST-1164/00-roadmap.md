# Roadmap: PYPOST-1164

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `documentation/PYPOST-1164-mcp-client-tab-mode-research`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1164/10-requirements.md` — MCP UX surface audit, doc/code gaps, competitive notes, MCP client tab mode functional requirements, child story breakdown (markdown table; Jira creation deferred)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1164/20-architecture.md` — UX options for protocol picker extension, TabProtocol relationship to PYPOST-1157…1163, architecture sketch, child story SP breakdown, proposed red tests
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change (PYPOST-1164 is research/decomposition only); red tests delegated to MCP-TM-1 … MCP-TM-8 per `20-architecture.md`
- [x] **STEP 4: Development**
  - N/A — research task; no `pypost/` code or tests added or changed
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1164/40-code-cleanup.md` — N/A for production code; Markdown artifact consistency review
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1164/50-observability.md` — N/A for research; `protocol=mcp_client` metrics deferred to MCP-TM-1
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1164/60-tech-debt.md` — pre-existing debt mapped to PYPOST-1165…1172
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_integration.md` — Planned: MCP client tab mode (PYPOST-1164) section
- [ ] **COMMIT: Commit Changes**

## Implementation Stories (Epic PYPOST-1155 — Phase D)

| Story | Jira | SP | Summary |
| --- | --- | --- | --- |
| MCP-TM-1 | [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) | 2 | Extend protocol picker with MCP Client |
| MCP-TM-2 | [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) | 5 | Blank MCP Client draft tab shell |
| MCP-TM-3 | [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169) | 5 | Tool discovery (`list_tools`) and browser UI |
| MCP-TM-4 | [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170) | 8 | Interactive `call_tool` + response pane |
| MCP-TM-5 | [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) | 3 | Outbound headers + environment templating |
| MCP-TM-6 | [PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171) | 5 | Migrate/remove HTTP method MCP |
| MCP-TM-7 | [PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172) | 5 | Collections save/open + context menu parity |
| MCP-TM-8 | [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168) | 2 | User documentation alignment |

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1164/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1164/20-architecture.md`

### STEP 3: Failing Repro

- N/A — research task

### STEP 4: Development

- N/A — research task

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1164/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1164/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1164/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_integration.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
