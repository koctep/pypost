# Roadmap: PYPOST-1534

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1534/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1534/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_http_client.py` — `TestHTTPClientBlankPathSegmentRejection.test_empty_path_origin_url_still_prepares`
  - Confirmed red: empty path raised `ExecutionError` / `blank_path_segment_rejected`
- [x] **STEP 4: Development**
  - [x] Early-return on empty `urlsplit(...).path` in `_assert_no_dot_path_segments` (keep mid-path / trailing blank + `.`/`..` rejects)
  - [x] `make test PYTEST_ARGS='tests/test_http_client.py'` green
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1534/40-code-cleanup.md`
  - `make lint` OK
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1534/50-observability.md` — N/A new signals; existing reject events unchanged
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1534/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/http_path_segment_rejection.md` (empty-path allow / PYPOST-1534)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1534/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1534/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_http_client.py::TestHTTPClientBlankPathSegmentRejection::test_empty_path_origin_url_still_prepares`

### STEP 4: Development

- `pypost/core/http_client.py` — empty-path allow in `_assert_no_dot_path_segments`
- Tests + docs as above

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1534/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1534/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1534/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/http_path_segment_rejection.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
