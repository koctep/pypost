# Roadmap: PYPOST-680

**Programming language:** Python 3.11+ (documentation and test updates; no new runtime code)

**Suggested branch:** `documentation/PYPOST-680-mcp-json-envelope-agent-guidance`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Updated `doc/mcp_integration.md` — JSON envelope parsing for agents/operators
  - [x] Updated `doc/dev/mcp_integration.md` — explicit `json.loads` agent guidance
  - [x] Updated `ai-tasks/PYPOST-552/cursor-verification-checklist.md` — envelope checks
  - [x] Updated `config/test/README.md` — Cursor envelope parsing note
  - [x] Extended `tests/test_mcp_user_docs.py` — doc envelope consistency checks
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

- `ai-tasks/PYPOST-680/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-680/20-architecture.md`

### STEP 3: Development

- `doc/mcp_integration.md`
- `doc/dev/mcp_integration.md`
- `ai-tasks/PYPOST-552/cursor-verification-checklist.md`
- `config/test/README.md`
- `tests/test_mcp_user_docs.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-680/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-680/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-680/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-680/70-dev-docs.md`
