# Roadmap: PYPOST-1386

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather business requirements: 60 FPS virtual scrolling for >1,000 selectors, minimal memory overhead, decoupled Model-View architecture, backward-compatible table API
  - [x] Document functional and non-functional requirements in `ai-tasks/PYPOST-1386/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design virtualized `HiddenFieldsTableModel(QAbstractTableModel)` and `HiddenFieldsTable(QTableView)` architecture with trailing row auto-expansion, backward-compatible facades, and 60 FPS virtualization in `ai-tasks/PYPOST-1386/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_hidden_fields_virtualization_repro.py`
- [x] **STEP 4: Development**
  - [x] Added `HiddenFieldsTableModel(QAbstractTableModel)` in `pypost/ui/models/hidden_fields_table_model.py` with trailing-row invariant, batch ops, and change signals
  - [x] Refactored `HiddenFieldsTable` to `QTableView` with model wiring, facades (`rowCount`/`item`), and preserved public API
  - [x] Step 3 repro green: `tests/test_hidden_fields_virtualization_repro.py` PASSED; related `tests/test_request_hidden_fields_model_and_ui.py` PASSED; `make lint` / `make typecheck` OK
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis via `make lint` + `make typecheck` (no `make analyze` target in repo)
  - [x] Cleaned repro suite: removed ImportError fallbacks, redundant per-test timeouts, shared `_SELECT_ROWS`
  - [x] Wrapped long `remove_rows` comprehension in `hidden_fields_table_model.py`
  - [x] Focused tests green: `test_hidden_fields_virtualization_repro.py`, `test_request_hidden_fields_model_and_ui.py`
  - [x] Cleanup report: `ai-tasks/PYPOST-1386/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Structured DEBUG logs on `HiddenFieldsTableModel` bulk `set_data`, trailing-row expand, `add_row`, `remove_rows`
  - [x] Artifact: `ai-tasks/PYPOST-1386/50-observability.md`
  - [x] Metrics: N/A for this UI virtualization refactor (existing mask/save metrics unchanged)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed model/view implementation, repro suite timeouts, architecture deviations, and observability trade-offs
  - [x] Artifact: `ai-tasks/PYPOST-1386/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/hidden_response_fields.md`: replaced stale `QTableWidget` description with Model/View (`QAbstractTableModel` + `QTableView`), facades, and PYPOST-1386 overview/section/references
  - [x] Added focused guide `doc/dev/hidden_fields_table.md` (architecture, API, observability, troubleshooting, tests)
  - [x] Indexed new doc from `doc/dev/README.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1386/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1386/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_hidden_fields_virtualization_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1386/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1386/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1386/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_fields_table.md` (new)
- `doc/dev/hidden_response_fields.md` (updated)
- `doc/dev/README.md` (index entry)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
