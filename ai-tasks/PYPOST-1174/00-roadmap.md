# Roadmap: PYPOST-1174

## Task Metadata

- **Implementation language**: Markdown

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1174/10-requirements.md`
  - Language: Markdown (Jira process and documentation artifacts; no Python product code)
  - Decision recorded: option (a) — rename PYPOST-1155 to a protocol-neutral title and
    fix epic labels; keep MCP stories parented under PYPOST-1155
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1174/20-architecture.md`
  - Option (a): rename PYPOST-1155; labels not websocket-only; keep children
  - Orchestrator applies Jira fields listed in `20-architecture.md` (no MCP here)
  - Failing-repro plan: N/A — no runtime behavioral change
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change (Jira fields and markdown only; no red test)
- [x] **STEP 4: Development**
  - [x] Wrote exact PYPOST-1155 Jira field values in `20-architecture.md` for orchestrator
  - [x] Aligned `ai-tasks/PYPOST-1164/00-roadmap.md` (option a + renamed epic)
  - [x] Aligned `ai-tasks/PYPOST-1164/10-requirements.md` (placement no longer open)
  - [x] Aligned `ai-tasks/PYPOST-1164/60-tech-debt.md` (placement closed as option a)
  - [x] Aligned `doc/dev/mcp_integration.md` (renamed epic + option a)
  - Jira MCP not called here; orchestrator applies `20-architecture.md` payload
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1174/40-code-cleanup.md`
  - Markdown-only: wrapped overlong Step 4 prose in PYPOST-1164 artifacts
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1174/50-observability.md`
  - N/A — no runtime logs or metrics (Jira + docs only)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1174/60-tech-debt.md`
  - No new follow-up tickets; Jira apply remains orchestrator-owned
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_integration.md` — Epic placement (PYPOST-1174) subsection
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1174/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1174/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (see STEP 3 in Step Status)

### STEP 4: Development

- Documentation updates (PYPOST-1164 artifacts + `doc/dev/mcp_integration.md`)
- Jira apply is orchestrator-owned (values in `20-architecture.md`)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1174/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1174/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1174/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_integration.md` (Epic placement subsection)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
