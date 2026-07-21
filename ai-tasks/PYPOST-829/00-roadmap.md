# Roadmap: PYPOST-829

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Approach C stress harness (`tests/test_storage_gateway_h3_stress.py`)
  - [x] H3 **confirmed**: segfault in `_on_worker_finished` under rapid
    churn + GC (both gateways); see `30-findings.md`
  - [x] Applied `deleteLater` + short `wait(100)` on both env and collection
    gateways; pending restart after capture/clear
  - [x] Stress + gateway + responsiveness isolation green (20 passed);
    suite-prefix crash in process_until is non-H3
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-829/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-829/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates
- `ai-tasks/PYPOST-829/30-findings.md` (H3 confirmed + fix evidence)

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-829/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-829/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-829/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/environment_storage_async.md`
- `doc/dev/collection_loading.md`
- `doc/dev/logging.md`
- `doc/dev/gui_testing.md`
- `ai-tasks/PYPOST-829/70-dev-docs.md`

## Suggested branch name

`fix/PYPOST-829-gateway-worker-finish-teardown`

