# Roadmap: PYPOST-1081

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `fix/PYPOST-1081-restore-log-file-capture`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1081/00-roadmap.md`
  - `ai-tasks/PYPOST-1081/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1081/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_log_capture_guardrail_repro.py`
- [x] **STEP 4: Development**
  - [x] Passed `log_config=None` to `uvicorn.Config` in `pypost/core/metrics_server.py`,
    `pypost/core/qt/mcp_server.py`, and `tests/helpers/mcp_live_server.py`
  - [x] Verified all 3 repro tests in `tests/test_log_capture_guardrail_repro.py` pass cleanly
  - [x] Curated `tests/expected_log_allowlist.yaml` baseline (146 errors) and added approved
    error patterns for legitimate negative/error tests
  - [x] Updated `tests/test_verify_test_log_guardrails.py` baseline assertion and verified
    `scripts/verify_test_log_guardrails.py` passes on full test log capture
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis and linting (`flake8`, `lint-docs`) on modified and created files
  - [x] Code formatting and line length checks (<= 100 chars)
  - [x] Cleanup temporary files (`pytest.log`)
  - [x] Verify tests pass with explicit timeout markers
  - [x] Create `ai-tasks/PYPOST-1081/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Structured log record format and level preservation (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
  - [x] Logging metrics and guardrail diagnostics (`scripts/verify_test_log_guardrails.py`)
  - [x] CI log guardrail verification validation (`.github/workflows/test.yml`)
  - [x] Create `ai-tasks/PYPOST-1081/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality, and deviations
  - [x] Verify missing tests and explicit timeout markers (`do-testing` compliance)
  - [x] Evaluate performance and log file I/O overhead
  - [x] Record follow-up tasks and pre-existing findings
  - [x] Create `ai-tasks/PYPOST-1081/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Create `doc/dev/test_log_guardrails.md` documenting log capture mechanics, `log_config=None` rationale, guardrail verifier, allowlist rules, and troubleshooting
  - [x] Update `doc/dev/README.md` table of contents
  - [x] Update `doc/dev/testing.md` and `doc/dev/logging.md` with cross-references and embedded uvicorn server guidelines
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1081/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1081/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1081/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1081/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1081/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
