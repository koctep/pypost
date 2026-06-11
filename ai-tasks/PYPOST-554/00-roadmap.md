# Roadmap: PYPOST-554

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `McpSecretsPolicy` module
  - [x] Wired `hidden_keys_supplier` through EnvPresenter → MCPServerManager → MCPServerImpl
  - [x] Applied policy to `list_tools` schema generation and execution logging
  - [x] Added unit and integration tests
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.11+ (PyPost project standard)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-554/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-554/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_secrets_policy.py`
- `pypost/core/mcp_server_impl.py`
- `pypost/core/mcp_server.py`
- `pypost/ui/presenters/env_presenter.py`
- `tests/test_mcp_secrets_policy.py`
- `tests/test_mcp_server_impl.py`
- `tests/test_env_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-554/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-554/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-554/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_secrets_policy.md`
- `doc/dev/mcp_integration.md` (updated)
