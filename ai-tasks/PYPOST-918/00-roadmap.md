# Roadmap: PYPOST-918

**Programming language:** Python (docs Markdown; packaging clarity /
deferral documentation — no product MCP surface change required)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *`tests/test_ui_actions_mcp_packaging_doc.py` (doc-token lock)*
- [x] **STEP 4: Development**
  - [x] Documented Option A packaging path in `doc/dev/ui_actions.md`
    (PYPOST-918, out-of-process, never mount on `MCPServerImpl`);
    cross-linked from `mcp_integration.md`, `mcp_trust_model.md`, and
    `agent_lifecycle.md`; doc-token contract tests green
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-918/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-918/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_actions_mcp_packaging_doc.py` (doc-token lock; red until
  Step 4 docs land)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-918/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-918/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-918/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/README.md` (index: UI actions + PYPOST-918 packaging)
- `doc/dev/ui_actions.md` (packaging path; Step 4)
- `doc/dev/mcp_integration.md` / `mcp_trust_model.md` / `agent_lifecycle.md`
- `ai-tasks/PYPOST-918/70-dev-docs.md`
