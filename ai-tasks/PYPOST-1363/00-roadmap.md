# Roadmap: PYPOST-1363

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_makefile_install_seed_contract.py::test_seed_minimal_project_conforms_to_flake8`
  - [x] `tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test`
  - [x] `tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Update `_seed_minimal_project` in `tests/makefile_test_helpers.py` to use
    two blank lines (`\n\n\n`) before `def test_noop()`, satisfying PEP 8 (E302).
  - [x] Verified Step 3 contract test `test_seed_minimal_project_conforms_to_flake8` passes.
  - [x] Verified integration tests `test_lint_succeeds_from_bare_venv_via_venv_test` and
    `test_lint_succeeds_after_install` pass.
  - [x] Verified `make lint` quality gate passes cleanly.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - [x] Analyzed diagnostic surface of test lint gate (`check_test_lint_baseline.py`).
  - [x] Analyzed diagnostic logging in Make tests (`_combined_output`, stderr capture).
  - [x] Verified contract test observability (`test_seed_minimal_project_conforms_to_flake8`).
  - [x] Documented runtime metrics assessment (N/A for test fixture scaffolding).
  - [x] Created `ai-tasks/PYPOST-1363/50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed shortcuts, code quality, test coverage, and performance.
  - [x] Documented pre-existing repository test failure tracked under PYPOST-1306.
  - [x] Created `ai-tasks/PYPOST-1363/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - [x] Documented isolated fixture seeding conventions and PEP 8 E302 requirements.
  - [x] Documented requirement for two blank lines (`\n\n\n`) preceding top-level definitions.
  - [x] Documented zero unbaselined findings contract for `scripts/check_test_lint_baseline.py`.
  - [x] Documented fast seed contract test in `tests/test_makefile_install_seed_contract.py`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1363/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1363/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_makefile_install_seed_contract.py::test_seed_minimal_project_conforms_to_flake8`
- `tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test`
- `tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install`

### STEP 4: Development

- `tests/makefile_test_helpers.py` (`_seed_minimal_project`)
- `tests/test_makefile_install_seed_contract.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1363/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1363/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1363/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (§ "Makefile automation tests" / "Test fixtures and isolated workspaces")

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
