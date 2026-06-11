# Roadmap: PYPOST-144

Suggested branch: `refactoring/PYPOST-144-template-service-di`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified `HTTPClient` and `MCPServerImpl` use constructor injection (PYPOST-45)
  - [x] Added `TestMCPServerImplInjection` for injected `TemplateService`
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

- `ai-tasks/PYPOST-144/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-144/20-architecture.md`

### STEP 3: Development

- `tests/test_mcp_server_impl.py` (injection test)
- Verification of existing injection in `pypost/core/http_client.py`,
  `pypost/core/mcp_server_impl.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-144/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-144/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-144/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/tech-debt/PYPOST-21.md` (section 2 marked resolved)
- `ai-tasks/PYPOST-144/70-dev-docs.md`
