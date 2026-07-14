# Roadmap: PYPOST-681

Programming language: Python 3.10+ (`.cursor/lsr/do-python.md`).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added optional `error_detail` to `format_structured_tool_result`
  - [x] Sanitized via `McpResponseSanitizer.sanitize_text`
  - [x] Unit tests for inclusion, omission, and redaction
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Suggested branch

`feature/PYPOST-681-mcp-error-detail`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-681/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-681/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_server_impl.py`
- `tests/test_mcp_server_impl.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-681/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-681/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-681/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-681/70-dev-docs.md`
- `doc/dev/mcp_integration.md`
