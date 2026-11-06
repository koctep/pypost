# Roadmap: PYPOST-1346

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1346/10-requirements.md`
  - Language: Python
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1346/20-architecture.md`
  - Fail-closed guard in `HTTPClient._prepare_request_kwargs` (rendered path segments `.` / `..`); shared seam noted for PYPOST-1332 blanks; `_urlencode` unchanged
  - Failing-repro plan: red `tests/test_http_client.py` + representative GitHub/GitLab offline `_prepare` cases
- [x] **STEP 3: Failing Repro Test**
  - Red tests (ExecutionError TEMPLATE not raised today; green FR4 controls pass):
    - `tests/test_http_client.py::TestHTTPClientDotPathSegmentRejection`
    - `tests/test_github_mcp_collection.py::test_github_prepare_rejects_dot_path_segments`
    - `tests/test_github_mcp_collection.py::test_github_prepare_allows_legitimate_dotted_workflow_id`
    - `tests/test_gitlab_mcp_collection.py::test_gitlab_prepare_rejects_dot_path_segments`
    - `tests/test_gitlab_mcp_collection.py::test_gitlab_prepare_allows_legitimate_file_path`
  - Confirmed via `make test` with targeted `PYTEST_ARGS`; no production changes
- [x] **STEP 4: Development**
  - [x] Implemented `_assert_no_dot_path_segments` and call it from `HTTPClient._prepare_request_kwargs` (TEMPLATE `ExecutionError`, origin-bounded ERROR log)
  - [x] Step 3 red tests green (`TestHTTPClientDotPathSegmentRejection`, GitHub/GitLab `_prepare` cases); FR4 controls still pass
  - [x] Aligned limitation wording in `examples/README.md`, `doc/dev/github_mcp_collection.md`, `doc/dev/gitlab_mcp_collection.md`
  - [x] Regenerated `ai-tasks/PYPOST-376/baseline-metrics.md` (`http_client` 381→409, within cap 418)
  - [x] Pre-existing suite failures triaged/deduped: PYPOST-1474, PYPOST-1475, PYPOST-1397 (see `60-tech-debt.md`)
  - [x] `make lint` + targeted/full Step 3 tests pass; `make test` clean aside from filed pre-existing set
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1346/40-code-cleanup.md`
  - `make lint` + `make typecheck` clean; scoped Step 3/4 tests green
  - Minor style: `_assert_no_dot_path_segments` uses `segment in (".", "..")`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1346/50-observability.md`
  - Documented existing ERROR `dot_path_segment_rejected` (origin-bounded via `_template_error_log_url`)
  - Registered allowlist prefix; baseline 146→164 (+18 intentional rejection ERRORs)
  - Added assertLogs regressions for event + origin-only URL safety
  - No new metrics (reuse `track_request_error(TEMPLATE)` via RequestService)
  - `make lint` + scoped `make test` green
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1346/60-tech-debt.md`
  - Documented literal-segment / blank-segment / `%2e` trade-offs; PYPOST-1332 linked (no new Jira)
  - Suite triage retained: NON-BLOCKER pre-existing → PYPOST-1474, PYPOST-1475, PYPOST-1397
  - No timeout BLOCKERs; no material performance debt
- [x] **STEP 8: Dev Docs**
  - `doc/dev/http_path_segment_rejection.md` (new: overview, architecture, reject/allow matrix, observability, troubleshooting)
  - Cross-links: `request_execution.md`, `logging.md`, `test_log_guardrails.md`, `github_mcp_collection.md`, `gitlab_mcp_collection.md`, `doc/dev/README.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1346/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1346/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_http_client.py` (`TestHTTPClientDotPathSegmentRejection`)
- `tests/test_github_mcp_collection.py` (dot-segment reject + `ci.yml` control)
- `tests/test_gitlab_mcp_collection.py` (dot-segment reject + file-path control)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1346/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1346/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1346/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/http_path_segment_rejection.md`
- Updated: `doc/dev/request_execution.md`, `doc/dev/logging.md`,
  `doc/dev/test_log_guardrails.md`, `doc/dev/github_mcp_collection.md`,
  `doc/dev/gitlab_mcp_collection.md`, `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
