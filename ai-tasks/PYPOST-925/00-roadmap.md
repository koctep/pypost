# Roadmap: PYPOST-925

**Programming language:** Python for pytest CI contract guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`) if Step 8
needs a light touch.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ci_make_install_smoke_qt_runtime.py` — PYPOST-925 red asserts
    (no `_PEER_QT_EGL_PACKAGES`; derived-only `_expected_qt_egl_packages()`)
- [x] **STEP 4: Development**
  - [x] Removed `_PEER_QT_EGL_PACKAGES`; added `_packages_from_apt_install_block()`
    and `_expected_qt_egl_packages()` parsing composite `action.yml` only
  - [x] Wired composite validation tests to derived helper; kept three-job `uses:`
    and inline-libegl1 sentinel tests unchanged
  - [x] All 8 contract tests green (`make test PYTEST_ARGS='...qt_runtime.py -v'`)
- [x] **STEP 5: Code Cleanup**
  - [x] Renamed misleading `test_make_install_smoke_has_full_peer_qt_egl_apt_set` →
    `test_composite_qt_egl_packages_inherited_by_qt_using_jobs`
  - [x] `make lint` + 8 contract tests green; `40-code-cleanup.md` created
- [x] **STEP 6: Observability**
  - [x] CI/contract only — application logging N/A; `50-observability.md` created
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` created; TD-2 resolved; no new Jira tickets
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-925/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-925/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-925/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-925/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-925/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
