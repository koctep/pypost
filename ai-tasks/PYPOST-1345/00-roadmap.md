# Roadmap: PYPOST-1345

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1345/10-requirements.md`
  - Language: Python (test-only debt; MCP collection verification)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1345/20-architecture.md`
  - Test-only: path-aware empty-body stub replies (201/202/204) + MCP success assertions
  - Failing-repro plan: dedicated red test in `tests/test_github_mcp_collection.py` (no stub/prod change in Step 3)
- [x] **STEP 3: Failing Repro Test**
  - Red test: `tests/test_github_mcp_collection.py::test_github_mcp_empty_body_write_success` (parametrized rerun-201 / cancel-202 / dispatch-204; fails on stub 200+JSON)
- [x] **STEP 4: Development**
  - [x] Path-aware empty-body stub replies (`/rerun`→201, `/cancel`→202, `/dispatches`→204)
  - [x] Generalized `_successful_envelope(expected_status, expect_empty_body)` + loopback e2e statuses
  - [x] Step 3 empty-body write success tests share the success helper
  - [x] `make test PYTEST_ARGS='tests/test_github_mcp_collection.py'` green; suite failures triaged as NON-BLOCKER (see `60-tech-debt.md`, new flake [PYPOST-1508](https://pypost.atlassian.net/browse/PYPOST-1508))
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1345/40-code-cleanup.md`
  - `make lint` + `make typecheck` clean; no unused imports/dead code/debug prints
  - Minor format: single-line `_EMPTY_BODY_WRITE_CASES` dispatch row
  - Scoped tests green (`empty_body_write_success`, `loopback_e2e_wire_contract`)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1345/50-observability.md`
  - N/A: test-only debt (stub + offline MCP assertions); no production logs/metrics
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1345/60-tech-debt.md` (full analysis + suite triage)
- [x] **STEP 8: Dev Docs**
  - Prefer update: `doc/dev/github_mcp_collection.md` (empty-body loopback stub 201/202/204)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1345/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1345/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_github_mcp_collection.py::test_github_mcp_empty_body_write_success`
  (parametrized: rerun-201, cancel-202, dispatch-204)

### STEP 4: Development

- `tests/helpers/github_mcp_collection_http.py` — path-suffix empty-body replies
- `tests/test_github_mcp_collection.py` — `_successful_envelope` + empty-body guard uses helper
- Triage notes seeded in `60-tech-debt.md` (full Step 7 analysis still pending)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1345/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1345/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1345/60-tech-debt.md` — full analysis (shortcuts, quality, missing
  tests, performance) + suite triage NON-BLOCKER table (PYPOST-1474/1475/1397/1492/1493/1508);
  no new Jira issues created this step

### STEP 8: Dev Docs

- `doc/dev/github_mcp_collection.md` — empty-body loopback stub (201/202/204), shared
  `_successful_envelope`, dedicated test + troubleshooting rows; PYPOST-1345 marked resolved

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
