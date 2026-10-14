# Roadmap: PYPOST-1377

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1377/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1377/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_request_hidden_fields_model_and_ui.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Extend `RequestData` with `hidden_response_fields: list[str] = Field(default_factory=list)` in `pypost/models/models.py`
  - [x] Iteration 2: Register `hidden_response_fields` in `_PERSISTED_FIELD_NAMES` and update `copy_request_for_isolated_tab()` in `pypost/core/request_persisted_fields.py`
  - [x] Iteration 3: Define `REQUEST_HIDDEN_FIELDS_TABLE = "request_hidden_fields_table"` in `pypost/ui/widget_ids.py`
  - [x] Iteration 4: Implement `HiddenFieldsTable` in `pypost/ui/widgets/hidden_fields_table.py` with auto-expanding empty row and data binding
  - [x] Iteration 5: Embed "Hidden Fields" detail tab into `RequestWidget` in `pypost/ui/widgets/request_editor.py` and wire load/save/extract/change handlers
  - [x] Iteration 6: Verify all 14 unit and UI tests pass, resolve mypy type check gate, and pass full test suite (406 files) and linting
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1377/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1377/50-observability.md`
  - [x] Documented logging, metrics, UI change events, and downstream observability requirements for hidden response fields.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1377/60-tech-debt.md`
  - [x] Analyzed shortcuts, code quality, test timeout markers, and performance; confirmed zero blockers for PYPOST-1377.
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/hidden_response_fields.md` (updated with MASK-1 architecture, model extension, dirty tracking, tab isolation, and UI components)
  - [x] `doc/user/requests.md` (added "Hidden fields" section with selector syntax and UI interaction guide)
  - [x] `ai-tasks/PYPOST-1377/70-dev-docs.md` (developer documentation record with verification instructions)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1377/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1377/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1377/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1377/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1377/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_response_fields.md`
- `doc/user/requests.md`
- `ai-tasks/PYPOST-1377/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
