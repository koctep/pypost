# Roadmap: PYPOST-792

**Branch (reference):** `bugfix/PYPOST-792-macos-tab-layout`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Iteration 1 (RC1): removed the active `QTabBar::tab { padding: 0 }` rule from
    `pypost/ui/styles/main.qss` (kept close-button icon rules, comment now warns against
    styling `::tab`); added `tests/test_tab_layout_regression.py` — QSS guard (no active
    `QTabBar::tab` rule) + geometry tests (sidebar and editor sub-tab labels get native
    padding, non-overlapping tab rects). 3/3 new tests pass.
  - [x] Iteration 2 (RC2): `PyPostStyle.close_button_size` now defaults to `None` and
    `pixelMetric` falls through to the base style unless `set_close_button_size` is called
    (opt-in override, API kept); dropped the forced `set_close_button_size(48)` calls in
    `pypost/main.py` and `StyleManager.apply_theme`. Added 4 close-indicator tests
    (default = base metric, override opt-in, `apply_theme("system")` native metrics,
    request-tab close button laid out at native size via `RequestTabHeader`). 7/7 pass.
  - [x] Iteration 3: added `check` target (`check: lint test` with `##` description) to the
    root `Makefile`; `make check` passes (flake8 clean, 1529 passed / 0 failed,
    1 deselected slow test, 61 subtests). Includes a fix for a pre-existing flake8 E402 in
    `pypost/ui/widgets/environments/environment_variables_widget.py` (module-level constant
    moved below the imports). Visual verification with the production styling
    pipeline under the native macOS style (light + dark): sidebar tabs, request tabs with
    close/`+` controls, and editor sub-tabs all render as separated native segments.
    Observation for Step 6: bundled `close.svg` (#666666 stroke) has low contrast on dark
    tab chrome at native size; hover state (`close-hover.svg`) is clearly visible.
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-792/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-792/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-792/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-792/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-792/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`
