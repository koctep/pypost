# Roadmap: PYPOST-1087

## Task Metadata

- **Implementation language**: YAML / Python docs
- **Branch name**: `debt/PYPOST-1087-allowlist-forward-looking-rule`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1087/00-roadmap.md`
  - `ai-tasks/PYPOST-1087/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1087/20-architecture.md`
- [x] **STEP 3: Failing Repro Test / Decision Verification**
  - Verified mechanism in `tests/test_verify_test_log_guardrails.py`.
- [x] **STEP 4: Development**
  - Annotated `tests/expected_log_allowlist.yaml` rule for `mcp_server_start_failed_ui` as forward-looking.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1087/40-code-cleanup.md`
  - `make lint` clean.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1087/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1087/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - No changes needed.
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1087/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1087/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_verify_test_log_guardrails.py`

### STEP 4: Development

- `tests/expected_log_allowlist.yaml`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1087/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1087/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1087/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message
