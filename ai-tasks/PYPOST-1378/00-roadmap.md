# Roadmap: PYPOST-1378

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1378/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1378/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_hidden_response_fields_masking.py`
- [x] **STEP 4: Development**
  - [x] Implement `redact_json_response_fields` with dot-notation, wildcard, and root-level selector matching in `pypost/core/sensitive_text_sanitizer.py`
  - [x] Update `McpResponseSanitizer.sanitize_body` in `pypost/core/mcp_response_sanitizer.py` to integrate hidden response fields redaction
  - [x] Wire `hidden_response_fields` from executed request into `format_structured_tool_result` and `MCPServerImpl._call_tool_inner` in `pypost/core/mcp_server_impl.py`
  - [x] Verify green repro test suite (14/14 tests pass in `tests/test_mcp_hidden_response_fields_masking.py`)
  - [x] Run quality gates (`make test`, `make lint`, `make typecheck`, `make verify-ai-tasks`, `make baseline-metrics`)
- [x] **STEP 5: Code Cleanup**
  - [x] Run quality checks (`make lint`, `make typecheck`, `make test PYTEST_ARGS="tests/test_mcp_hidden_response_fields_masking.py"`, `make verify-ai-tasks`)
  - [x] Inspect modified files for PEP 8, line length <= 100, unused imports, dead/debug code, and test timeout markers
  - [x] Create `ai-tasks/PYPOST-1378/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1378/50-observability.md`
  - [x] Documented logging, metrics, fallback behavior, and security audit log boundaries for permanent MCP response masking.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1378/60-tech-debt.md`
  - [x] Evaluated shortcuts taken, code quality issues, missing tests, and performance concerns.
  - [x] Verified zero tests missing timeout markers across test suites (`tests/test_mcp_hidden_response_fields_masking.py` guarded by `pytest.mark.timeout(60)`).
  - [x] Classified follow-up tasks into blockers vs non-blockers (confirmed 0 blockers; PYPOST-1379 and PYPOST-1380 tracked in Sprint 2032).
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/hidden_response_fields.md` with MASK-2 permanent MCP response masking architecture details.
  - [x] Create `doc/dev/mcp.md` documenting response field masking security guarantees for MCP client agents.
  - [x] Create `ai-tasks/PYPOST-1378/70-dev-docs.md` developer documentation record per td-70-dev-docs template.
  - [x] Run `make lint` and `make verify-ai-tasks`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1378/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1378/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_hidden_response_fields_masking.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1378/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1378/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1378/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_response_fields.md`
- `doc/dev/mcp.md`
- `ai-tasks/PYPOST-1378/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
