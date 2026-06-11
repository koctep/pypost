# Roadmap: PYPOST-407

**Suggested branch:** `refactoring/PYPOST-407-request-data-copy-policy`

**Programming language:** Python 3.10+

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `copy_request_for_isolated_tab` in `request_sync.py` and routed tab-isolation
        call sites through it
  - [x] Documented copy policy on `RequestData` and in `doc/dev/request_data_copy_policy.md`
  - [x] Added `tests/test_request_sync.py` for copy semantics and lean-model guard
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

- `ai-tasks/PYPOST-407/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-407/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-407/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-407/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-407/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/request_data_copy_policy.md`
- `doc/dev/open_request_in_isolated_tab.md` (updated)
