# Roadmap: PYPOST-943

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - Primary repro: `tests/test_makefile.py::TestSlowInstallSmoke::test_install_succeeds_with_project_pyproject` (existing, red on HEAD)
  - Fast seed-contract guard: `tests/test_makefile_install_seed_contract.py`
- [x] **STEP 4: Development**
  - [x] Added `_seed_installable_package` copying repo `pypost/version.py` and `README.md`
        into slow-smoke isolated workspace; wired `make_workspace_full_deps` and seed
        contract test to use it — both Step 3 red tests green
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - Documented N/A for runtime logging/metrics; CI and test assertion signals
    recorded in `50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - Created `60-tech-debt.md`; verdict SAFE TO CLOSE; five Low/Lowest follow-ups
    for Phase D (no Jira tickets in this step)
- [x] **STEP 8: Dev Docs**
  - [x] Note in `doc/dev/testing.md`: slow smoke seed mirrors packaging metadata
  - [x] Refreshed `ai-tasks-artifacts-baseline.json` (TD-5 / PYPOST-967)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest contract / smoke tests, `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Makefile and CI workflow remain the primary
automation interface. Developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-943/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-943/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-943/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-943/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-943/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
