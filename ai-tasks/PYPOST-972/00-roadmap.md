# Roadmap: PYPOST-972

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change: production already raises
    `UiTargetNotInteractableError` with `"item view has no model"` when
    `QListView.model()` is `None` (`_select_item_view`). Classic
    red-before-green does not apply; do not leave a permanent red test.
    Dedicated green contract test deferred to Step 4
    (`test_select_list_view_no_model_raises`).
- [x] **STEP 4: Development**
  - [x] Added `test_select_list_view_no_model_raises` — QListView with no
    model raises `UiTargetNotInteractableError` with
    `"item view has no model"` (distinct from tree reason); no production
    changes.
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` clean; module `timeout(60)` inherited; 33 passed in
    `tests/test_ui_actions.py`; artifact `40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] No-new-log / no metrics (NFR-4); artifact `50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] SAFE TO CLOSE; tree no-model coverage noted as TD-1 follow-up;
    artifact `60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/ui_actions.md` + `doc/dev/testing.md`; artifact
    `70-dev-docs.md`

## Suggested branch

`test/PYPOST-972-item-view-no-model`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-972/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-972/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (classic red-before-green not applicable;
  see Step Status). Contract test lands in Step 4.

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-972/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-972/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-972/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`
- `doc/dev/testing.md`
- `ai-tasks/PYPOST-972/70-dev-docs.md`
