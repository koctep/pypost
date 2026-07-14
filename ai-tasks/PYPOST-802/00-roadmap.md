# Roadmap: PYPOST-802

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Introduced `RequestFields` in `pypost/core/request_fields.py` with semantic aliases
  - [x] Removed duplicate dataclass definitions from `http_client.py` and
    `sensitive_data_masking_policy.py`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.11+ (PyPost core)

## Suggested Branch

`refactoring/PYPOST-802-shared-request-fields-type`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-802/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-802/20-architecture.md`

### STEP 3: Development

- `pypost/core/request_fields.py`
- `pypost/core/http_client.py`
- `pypost/core/sensitive_data_masking_policy.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-802/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-802/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-802/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/sensitive_data_masking_policy.md`
