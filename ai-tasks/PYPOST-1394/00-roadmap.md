# Roadmap: PYPOST-1394

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1394/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1394/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_pypost_1394_failing_repro.py`
- [x] **STEP 4: Development**
  - [x] Implement `pypost/core/json_selector_engine.py` and turn repro green
  - [x] Integrate `JsonSelectorEngine` into `SensitiveTextSanitizer`
  - [x] Integrate `JsonSelectorEngine` into `ResponseMaskController` (`JsonMaskFormatter`)
  - [x] Quality gate and test verification (all repro and regression suites green)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1394/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1394/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1394/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/json_selector_engine.md` — unified JSON selector path evaluation engine documentation
  - [x] `doc/dev/hidden_response_fields.md` — cross-links to unified engine and PYPOST-1394 architecture
  - [x] `doc/dev/README.md` — table of contents index update
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1394/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1394/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1394/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1394/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1394/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/json_selector_engine.md`
- `doc/dev/hidden_response_fields.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
