# Roadmap: PYPOST-924

**Programming language:** GitHub Actions workflow YAML for CI step consolidation;
Python for pytest contract guards (`.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ci_make_install_smoke_qt_runtime.py` — red tests:
    - `test_install_qt_egl_composite_action_exists_with_full_package_set`
    - `test_qt_using_jobs_reference_install_qt_egl_composite`
    - `test_workflow_has_zero_inline_libegl1_apt_install_blocks`
- [x] **STEP 4: Development**
  - [x] Added `.github/actions/install-qt-egl-runtime/action.yml` composite with eight-package apt set
  - [x] Wired `test`, `make-install-smoke`, and `agent-e2e` in `test.yml` to `uses: ./.github/actions/install-qt-egl-runtime`; removed three inline apt blocks
  - [x] Adapted `test_make_install_smoke_has_full_peer_qt_egl_apt_set` to assert composite `uses:` + package parity via `action.yml`
  - [x] All five contract tests green (`make test PYTEST_ARGS='tests/test_ci_make_install_smoke_qt_runtime.py -v'`)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-924/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-924/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-924/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-924/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-924/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
