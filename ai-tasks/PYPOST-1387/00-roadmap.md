# Roadmap: PYPOST-1387

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1387/10-requirements.md`
  - Language: Python
  - Business goal: prevent silent masking failures by giving users live feedback when selector expressions are invalid or unsupported
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1387/20-architecture.md`
  - Pure core `validate_field_selector` + model Background/ToolTip roles + advisory `FieldSelectorDelegate`
  - Failing-repro plan: `tests/test_field_selector_syntax.py` + `tests/test_hidden_fields_syntax_validation_repro.py`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_field_selector_syntax.py` — red (`ModuleNotFoundError: pypost.core.field_selector_syntax`)
  - `tests/test_hidden_fields_syntax_validation_repro.py` — red (invalid rows lack `BackgroundRole` highlight / guidance tooltip)
  - Review fix: ToolTipRole guidance assert requires errorish wording **and** a supported-form example not present in the static help string (so `"dot"` no longer false-greens)
- [x] **STEP 4: Development**
  - [x] Added `pypost/core/field_selector_syntax.py` (`FieldSelectorSyntaxResult`, `validate_field_selector`)
  - [x] Extended `HiddenFieldRecord` / `HiddenFieldsTableModel` with cached syntax + `BackgroundRole` / conditional `ToolTipRole`
  - [x] Added advisory `FieldSelectorDelegate` and wired it from `HiddenFieldsTable`
  - [x] Step 3 repros green: `tests/test_field_selector_syntax.py`, `tests/test_hidden_fields_syntax_validation_repro.py`
  - [x] `make lint` + `make typecheck` OK; related Hidden Fields tests green
  - [x] Full `make test` triage: remaining failures pre-existing (see `60-tech-debt.md`)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1387/40-code-cleanup.md`
  - Typed `FieldSelectorDelegate` Qt overrides; dropped unused `_make_record` alias
  - Refreshed stale red-phase test docstrings; removed redundant snippet entry
  - `make lint` + `make typecheck` OK; focus tests 2/2 PASSED
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1387/50-observability.md`
  - Extended `HiddenFieldsTableModel` DEBUG: `set_data` syntax counts
    (`ok_count` / `invalid_count` / `empty_count`); per-cell
    `set_data_cell` with `ok` / `is_empty` / `selector_len`; `add_row` `ok=`
  - No logs in `validate_field_selector` or live delegate keystroke path
    (avoids DEBUG flood); no new metrics
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1387/60-tech-debt.md` rewritten to skill template
  - Implementation debt: header-prefix duplication, `..` false-green after
    wildcard normalize, generic invalid messages, no delegate live-test,
    no header sync assertion; timeouts OK (no BLOCKER)
  - Pre-existing suite failures retained with Jira keys (PYPOST-1534/1535/1536,
    1474, 1397, 1492, 1475)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_fields_table.md` — documented `validate_field_selector`,
    `FieldSelectorDelegate`, `BackgroundRole` / `ToolTipRole`, vocabulary,
    advisory flow, observability, troubleshooting, and tests
  - `doc/dev/hidden_response_fields.md` — PYPOST-1387 cross-refs in overview,
    table API, §6 virtualization, and references
  - `doc/dev/README.md` — index titles include PYPOST-1387
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1387/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1387/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_field_selector_syntax.py`
- `tests/test_hidden_fields_syntax_validation_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1387/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1387/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1387/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_fields_table.md`
- `doc/dev/hidden_response_fields.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
