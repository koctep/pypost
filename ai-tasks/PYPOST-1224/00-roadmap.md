# Roadmap: PYPOST-1224

## Task Metadata

- **Implementation language**: Python / Markdown / JSON / YAML

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1224/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1224/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_examples_modernization_repro.py`
- [x] **STEP 4: Development**
  - [x] `examples/pypost-library.yaml` (created canonical library manifest)
  - [x] `examples/collections/jira_mcp.json` (modernized with embedded variable declarations)
  - [x] `examples/README.md` (updated with Library Manager and manifest documentation)
  - [x] `tests/fixtures/legacy_collections/` (archived legacy format fixtures)
  - [x] `tests/test_examples_modernization.py` (comprehensive regression test suite)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1224/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1224/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1224/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/examples_library_format.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1224/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1224/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_examples_modernization_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1224/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1224/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1224/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
