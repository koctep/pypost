# Roadmap: PYPOST-1173

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1173/10-requirements.md`
  - Implementation language recorded: Python
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1173/20-architecture.md`
  - Wiring-only change: pass `resolved_headers` from `_execute_mcp` into `MCPClientService.run` → `create_mcp_http_client(headers=...)`
  - Failing-repro design: `tests/test_mcp_client_service.py` (headers reach factory) + `tests/test_request_service.py` (resolved headers forwarded)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_client_service.py::MCPClientServiceTests::test_run_passes_headers_to_create_mcp_http_client`
  - `tests/test_request_service.py::TestRequestServiceMCP::test_execute_mcp_forwards_resolved_headers_to_mcp_client`
  - `tests/test_request_service.py::TestRequestServiceMCP::test_execute_mcp_forwards_empty_headers_to_mcp_client`
- [x] **STEP 4: Development**
  - [x] Wired resolved MCP headers through `MCPClientService.run` → `create_mcp_http_client(headers=..., timeout=...)` and `RequestService._execute_mcp` (`headers=resolved_headers`); Step 3 red tests green.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1173/40-code-cleanup.md`
  - Hanging indent on `create_mcp_http_client(headers=..., timeout=...)`
  - `make lint` passed; `make test` 271 passed / 0 failed / 1 skipped (unrelated)
  - `make typecheck`: no PYPOST-1173 errors; pre-existing baseline drift elsewhere
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1173/50-observability.md`
  - `mcp_operation_start` now includes `header_count` (never header values)
  - Tests: `test_run_logs_header_count_not_values`,
    `test_run_logs_zero_header_count_when_headers_omitted`
  - No new metrics — existing MCP Send counters already cover this path
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1173/60-tech-debt.md`
  - No PYPOST-1173-specific debt (wiring matches architecture)
  - Follow-up: flaky `test_update_tools_restarts_when_exposed_set_changes`
    (NON-BLOCKER — pre-existing/flaky; Jira pending)
  - Pre-existing `make typecheck` baseline drift noted (NON-BLOCKER)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_integration.md` — method-MCP header forwarding (PYPOST-1173); MCP-TM-5 still
    planned for the MCP Client tab
  - `doc/dev/logging.md` — `mcp_operation_start` `header_count`; Sensitive Data: never keys/values
  - `doc/dev/request_execution.md` — `_execute_mcp` / `MCPClientService.run` forward headers
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1173/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1173/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1173/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1173/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1173/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
