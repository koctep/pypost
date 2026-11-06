# Roadmap: PYPOST-1332

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1332/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1332/20-architecture.md`
  - Extends PYPOST-1346 `_prepare_request_kwargs` / path-segment seam for blank segments
  - Always-on fail-closed (not opt-in required-flag)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_http_client.py` — `TestHTTPClientBlankPathSegmentRejection`
  - `tests/test_gitlab_mcp_collection.py` — `test_gitlab_prepare_rejects_blank_path_segments`
  - `tests/test_github_mcp_collection.py` — `test_github_prepare_rejects_blank_path_segments`
  - Confirmed red before production fix (blank segments still prepared)
- [x] **STEP 4: Development**
  - [x] Extended `_assert_no_dot_path_segments` to reject blank segments (skip only leading absolute `/` empty)
  - [x] `blank_path_segment_rejected` ERROR log + allowlist; baseline_error_count 164→165
  - [x] Core + GitLab/GitHub blank prepare tests green; dot suite remains green
  - [x] Dev/collection/README docs aligned with fail-closed blanks
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1332/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1332/50-observability.md`
  - Event: `blank_path_segment_rejected` (origin-bounded URL)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1332/60-tech-debt.md`
  - No new Jira creates
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/http_path_segment_rejection.md`, `request_execution.md`, `logging.md`,
    `test_log_guardrails.md`, `testing.md`, GitLab/GitHub collection docs, `examples/README.md`
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[x]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1332/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1332/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_http_client.py` (`TestHTTPClientBlankPathSegmentRejection`)
- `tests/test_gitlab_mcp_collection.py` / `tests/test_github_mcp_collection.py` blank prepares

### STEP 4: Development

- `pypost/core/http_client.py`
- Tests + allowlist + docs

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1332/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1332/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1332/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/http_path_segment_rejection.md` (and related updates)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
