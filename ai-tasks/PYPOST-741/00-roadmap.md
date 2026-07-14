# Roadmap: PYPOST-741

**Programming language:** Python

**Parent audit:** [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) — observability and
logging audit

**Finding:** R-P1-001 / L-001 (PYPOST-685 E-003) — resolved URLs in `http_client` ERROR logs

**Suggested branch:** `fix/PYPOST-741-redact-http-error-urls`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `_error_log_url` helper + four ERROR path updates
  - [x] Expanded `TestHTTPClientErrorLogging` (5 cases)
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

- `ai-tasks/PYPOST-741/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-741/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-741/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-741/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-741/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`
