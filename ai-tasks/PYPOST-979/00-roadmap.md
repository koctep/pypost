# Roadmap: PYPOST-979

## Programming Language

Python (pytest + Qt UI wait helpers; `.cursor/lsr/do-python.md`).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change
  - Characterizing multi-tab proofs deferred to Step 4 (`tests/test_ui_wait.py`)
- [x] **STEP 4: Development**
  - [x] Added multi-tab characterizing proofs in `tests/test_ui_wait.py`:
    `test_session_wait_for_widget_in_current_tab_multi_tab` (identity +
    rename isolation) and
    `test_session_wait_for_enabled_in_current_tab_multi_tab` (disable
    isolation + re-enable identity); no production or doc changes
    (contract already accurate)
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` clean; `flake8` clean on `tests/test_ui_wait.py`;
    scoped multi-tab proofs passed; no cleanup fixes required
    (`ai-tasks/PYPOST-979/40-code-cleanup.md`)
- [x] **STEP 6: Observability**
  - [x] N/A for new instrumentation — tests reuse existing `ui_wait_*`
    timeout diagnostics; documented in
    `ai-tasks/PYPOST-979/50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] Reviewed multi-tab proofs vs FR/AC; no task-owned follow-up debt
    (`ai-tasks/PYPOST-979/60-tech-debt.md`); closes PYPOST-949 TD-2
- [x] **STEP 8: Dev Docs**
  - [x] Verified `doc/dev/ui_wait.md` tab-scoped wait contract; cited
    multi-tab widget/enabled proofs (PYPOST-979) alongside text
    (PYPOST-949); `agent_e2e.md` / related docs had no inaccurate
    coverage claims

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-979/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-979/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (session `wait_for_widget` /
  `wait_for_enabled` already route via `_action_root(in_current_tab=…)`;
  multi-tab characterizing proofs belong in Step 4)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-979/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-979/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-979/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### Suggested branch (reference only)

`test/PYPOST-979-tab-scoped-wait-widget-enabled`
