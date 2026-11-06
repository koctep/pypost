# Roadmap: PYPOST-1333

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1333/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1333/20-architecture.md`
  - Design: sanitize-at-raise via `_error_log_url` + SSE one-line switch +
    request_service `sanitize_text` defense in depth
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_http_client.py::TestHTTPClientErrorLogging::test_timeout_execution_error_message_redacts_resolved_url`
  - `tests/test_http_client.py::TestHTTPClientErrorLogging::test_connection_execution_error_message_redacts_resolved_url`
  - `tests/test_http_client.py::TestHTTPClientSSEStreamLogging::test_sse_stream_detected_logs_redacted_resolved_url`
  - `tests/test_retry.py::TestRetryLogSanitization::test_retryable_error_log_redacts_url_in_error_message`
  - `tests/test_retry.py::TestRetryLogSanitization::test_exhaustion_alert_message_redacts_url`
  - Confirmed red on unsanitized `token=abc` before Step 4 fix
- [x] **STEP 4: Development**
  - [x] `HTTPClient` timeout/connection messages use `_error_log_url`
  - [x] `sse_stream_detected` logs `_error_log_url`
  - [x] `RequestService` wraps retry/alert error messages with `sanitize_text`
  - Focused tests green after fix
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1333/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1333/50-observability.md` (harden existing sinks; no new events)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1333/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/logging.md`, `gitlab_mcp_collection.md`,
    `github_mcp_collection.md`, `observability_audit.md`
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[x]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1333/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1333/20-architecture.md`

### STEP 3: Failing Repro

- Automated red tests under `tests/test_http_client.py` and `tests/test_retry.py`

### STEP 4: Development

- `pypost/core/http_client.py`
- `pypost/core/request_service.py`
- Tests above

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1333/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1333/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1333/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/logging.md`
- `doc/dev/gitlab_mcp_collection.md`
- `doc/dev/github_mcp_collection.md`
- `doc/dev/observability_audit.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
