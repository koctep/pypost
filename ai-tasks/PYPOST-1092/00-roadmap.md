# Roadmap: PYPOST-1092

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `feature/PYPOST-1092-mcp-proxy-upstream-env-headers`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_proxy_server.py`
- [x] **STEP 4: Development**
  - [x] Extend `McpServerConfiguration` model with proxy fields (`server_type`, `upstream_url`, `upstream_transport`, `headers`, `timeout`) and validation
  - [x] Implement dynamic header template resolution and secret sanitization in `pypost/core/mcp_proxy_headers.py`
  - [x] Implement `MCPProxyServerImpl` forwarding tools, prompts, and resources over Streamable HTTP and SSE with secret masking in `pypost/core/mcp_proxy_server_impl.py`
  - [x] Integrate proxy server lifecycle into `MCPServerManager` and `MCPServerRegistry`
  - [x] Enhance UI dialogs and editor in `pypost/ui/dialogs/mcp_servers_dialog.py` for proxy server management and validation
  - [x] Verify repro test suite and full project test suite and linters pass cleanly
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**
  - Commit hash: `d75b3d34` on `dev` — "feature(mcp): PYPOST-1092 support upstream MCP proxy with env header resolution"
  - Branch name (reference only, not switched): `feature/PYPOST-1092-mcp-proxy-upstream-env-headers`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1092/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1092/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1092/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1092/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1092/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
