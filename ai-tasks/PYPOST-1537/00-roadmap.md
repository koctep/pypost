# Roadmap: PYPOST-1537

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1537/10-requirements.md`
  - Language: Python
  - Business goal: warn while a hidden-field selector is being typed, and keep
    an invalid draft when editing finishes
  - Done when one automated check proves live warning, neutral feedback, and advisory accept
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1537/20-architecture.md`
  - Live warning and advisory commit already exist; no production change
  - Step 3 is N/A — no behavioral change; the check lands in Step 4
  - Planned check: `tests/test_hidden_fields_open_edit.py`
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change. The open edit already warns on `$.secret`,
    stays neutral on `token`, and keeps `$.secret` on finish; the check is a
    Step 4 deliverable.
- [x] **STEP 4: Development**
  - [x] Added `tests/test_hidden_fields_open_edit.py`: open `$.secret` warns,
    open `token` stays neutral, and finishing keeps `$.secret`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1537/40-code-cleanup.md`
  - `make analyze` is not a target; `make lint` passed
  - `tests/test_hidden_fields_open_edit.py` was not edited: lint-clean, longest
    line 85, module timeout `pytest.mark.timeout(30)`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1537/50-observability.md`
  - No logs or metrics added. The delegate does not log the open edit.
    `HiddenFieldsTableModel.setData` already logs the commit that ends the
    edit: length and syntax flags only, not selector text.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1537/60-tech-debt.md`
  - No new debt. The check drives the open editor with `setText`, and the
    module timeout is `pytest.mark.timeout(30)`.
  - User docs under `doc/` stay unchanged: this task does not change
    user-visible behavior. Developer docs stay with Step 8.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_fields_table.md` Tests:
    `make test PYTEST_ARGS="tests/test_hidden_fields_open_edit.py"`
  - Note: PYPOST-1537 covers the open edit of existing behavior, not a product change
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1537/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1537/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1537/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1537/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1537/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
