# Roadmap: PYPOST-1536

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1536/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1536/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - Existing red (under parallel load): `tests/test_async_manifest_discovery_repro.py::test_dialog_init_does_not_block_on_slow_manifest_discovery`
  - Failure excerpt (base `7b4d31be` full suite): `AssertionError: Dialog __init__ blocked for 0.241s` — false positive; Qt setup alone ~138ms before discovery started
  - Repro: `make test PYTEST_ARGS='tests/test_async_manifest_discovery_repro.py::test_dialog_init_does_not_block_on_slow_manifest_discovery -vv --tb=short'`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Replace brittle wall-clock `<0.1s` assert with threading.Event gate + off-UI-thread check for `list_connections`; product path unchanged (`ManifestDiscoveryWorker`)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1536/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1536/50-observability.md` (N/A — test-only)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1536/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/workspace_environment_variable_import.md` (non-blocking init test contract)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1536/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1536/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_async_manifest_discovery_repro.py::test_dialog_init_does_not_block_on_slow_manifest_discovery`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1536/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1536/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1536/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
