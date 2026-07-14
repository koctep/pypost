# Roadmap: PYPOST-751

**Programming language:** Python

**Parent audit:** [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) — observability and
logging audit

**Finding:** R-P3-003 / O-002 — legacy human-readable ERROR prefixes in `http_client`

**Suggested branch:** `refactor/PYPOST-751-http-client-log-events`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Migrate three ERROR log events to key=value format
  - [x] Update allowlist and error-logging tests
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-751/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-751/20-architecture.md`

### STEP 3: Development

- `pypost/core/http_client.py`
- `tests/test_http_client.py`
- `tests/expected_log_allowlist.yaml`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-751/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-751/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-751/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/logging.md`
- `doc/dev/observability_audit.md`
