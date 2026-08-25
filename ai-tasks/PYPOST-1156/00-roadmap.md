# Roadmap: PYPOST-1156

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `documentation/PYPOST-1156-websocket-tab-mode-research`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1156/10-requirements.md` — tab-creation audit, doc/code gaps, MCP alignment, child story breakdown
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1156/20-architecture.md` — UX options (popup menu recommended), component diagram, child stories with SP
  - Jira child stories created under [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155): PYPOST-1157 … PYPOST-1163 (WS-TM-1 … WS-TM-7)
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change (PYPOST-1156 is research/decomposition only); red tests delegated to PYPOST-1157…1163
- [x] **STEP 4: Development**
  - N/A — no production code in this research task
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1156/40-code-cleanup.md` — N/A for research task
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1156/50-observability.md` — metrics protocol label deferred to PYPOST-1157
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1156/60-tech-debt.md` — pre-existing debt routed to PYPOST-1157…1163
- [x] **STEP 8: Dev Docs**
  - `doc/dev/websocket_ui_client.md` — Planned: blank-tab WebSocket mode section
- [x] **COMMIT: Commit Changes**
  - `6fe22673` — documentation(websocket): PYPOST-1156 research WebSocket tab mode UX

## Implementation Stories (Epic PYPOST-1155 — created in Step 2)

| Story | Jira | SP | Summary | Depends on |
| --- | --- | ---: | --- | --- |
| WS-TM-1 | [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) | 3 | Blank-tab protocol selector UX | — |
| WS-TM-2 | [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) | 5 | Blank WebSocket draft tab | WS-TM-1 |
| WS-TM-3 | [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159) | 2 | Tab entry-point parity | WS-TM-1, WS-TM-2 |
| WS-TM-4 | [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160) | 3 | Collections WebSocket menu parity | WS-TM-2 |
| WS-TM-5 | [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161) | 5 | WebSocket save-to-collection flow | WS-TM-2 |
| WS-TM-6 | [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162) | 3 | Context-aware WebSocket shortcuts | WS-TM-2 |
| WS-TM-7 | [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163) | 2 | User documentation alignment | WS-TM-1 … WS-TM-6 |

**Total:** 23 SP. Suggested order: WS-TM-1 → WS-TM-2 → WS-TM-3 → WS-TM-5 → WS-TM-6 → WS-TM-4 → WS-TM-7.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1156/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1156/20-architecture.md`

### STEP 3: Failing Repro

- N/A — research task

### STEP 4: Development

- N/A — research task

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1156/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1156/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1156/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_ui_client.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
