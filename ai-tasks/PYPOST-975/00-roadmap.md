# Roadmap: PYPOST-975

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — no behavioral change* (`_select_tree` already raises
    `option not found` / `option index out of range` via
    `session.ui_select` on live `COLLECTION_TREE`; Path A live contract
    proofs expected green on first run in Step 4 — no red-before-green)
  - [x] Review passed N/A (sprint-task-runner autonomous; no user gate)
- [x] **STEP 4: Development**
  - [x] Added Path A live proofs in `tests/test_ui_actions.py`:
    `test_live_collection_tree_missing_option_raises` and
    `test_live_collection_tree_index_out_of_range_raises` via
    `seeded_agent_e2e_session` (fixture-parity substrings; production
    unchanged)
- [x] **STEP 5: Code Cleanup**
  - [x] Flake8/`make lint` clean; live tests polished; `40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] N/A new production logging/metrics (NFR-4 / AC-5); documented
    existing `_select_tree` exception + success DEBUG coverage in
    `50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE; no new unticketed Debt; Path A
    DoD met; docs cite deferred to Step 8; mypy / table nits accepted
- [x] **STEP 8: Dev Docs**
  - [x] Cited live `COLLECTION_TREE` negative select proofs in
    `doc/dev/ui_actions.md`, `doc/dev/testing.md`, `doc/dev/agent_e2e.md`
    (fixture negatives retained; PYPOST-975)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6 agent UI actions and agent e2e harness)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-975/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-975/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (see architecture § Mandatory — Failing Repro)
- Rationale: production `_select_tree` already raises
  `UiTargetNotInteractableError` with `option not found` /
  `option index out of range` on the live product tree via
  `session.ui_select`. This task adds live agent e2e regression/contract
  coverage (expected green on first run). Classic red-before-green does
  not apply; do not leave a permanent red test. Planned proofs deferred
  to Step 4:
  - `test_live_collection_tree_missing_option_raises`
  - `test_live_collection_tree_index_out_of_range_raises`
  (in `tests/test_ui_actions.py` with `seeded_agent_e2e_session`)
- Confirmed: no automated red test under `tests/`; no production code
  changed in this step
- Review passed N/A (sprint-task-runner autonomous)

### STEP 4: Development

- Source code
- Tests
- Documentation updates
- Path A live `COLLECTION_TREE` negative select proofs (missing label +
  top-level OOR) in `tests/test_ui_actions.py`; production unchanged

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-975/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-975/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-975/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md` — live `COLLECTION_TREE` negative select proofs
- `doc/dev/testing.md` — same live proofs alongside PYPOST-942 fixtures
- `doc/dev/agent_e2e.md` — harness table note for `tests/test_ui_actions.py`

## Suggested Branch Name

`test/PYPOST-975-live-collection-tree-negatives`
