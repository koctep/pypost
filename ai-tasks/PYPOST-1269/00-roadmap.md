# Roadmap: PYPOST-1269

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1269/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_runtime_distribution_modes.py`
- [x] **STEP 4: Development**
  - [x] Declared `pypost = "pypost.main:main"` in `[project.scripts]` in `pyproject.toml`.
  - [x] Created `pypost/__main__.py` package execution entrypoint delegating to `pypost.main.main()`.
  - [x] Added `build_parser()` and `argv` argument parsing to `pypost/main.py`.
  - [x] Replaced `PySide6.QtWidgets.QApplication` with `PySide6.QtCore.QCoreApplication` in `EnvironmentStorageGateway.wait_idle()`.
  - [x] Extended `scripts/check_package_data.py` to inspect `entry_points.txt` in wheel `.dist-info` for console scripts `pypost` and `pypost-daemon`.
  - [x] Synchronized `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` in `tests/makefile_test_helpers.py` to include `main.py`.
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1269/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1269/50-observability.md`
  - [x] Documented logging catalog, lifecycle events, and metrics parity for GUI and daemon runtimes.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1269/60-tech-debt.md`
  - [x] Documented shortcuts taken, code quality issues, missing tests, and performance concerns.
  - [x] Audited timeout markers: zero tests missing timeout markers across test suites.
  - [x] Classified follow-up items as non-blockers (zero blockers for closing PYPOST-1269).
- [x] **STEP 8: Dev Docs**
  - [x] `ai-tasks/PYPOST-1269/70-dev-docs.md`
  - [x] Updated `doc/dev/daemon.md`: documented dual distribution modes (`pypost` and `pypost-daemon`), architectural decoupling invariants, and wheel entry points validation.
  - [x] Updated `doc/dev/README.md`: indexed dual runtime distribution modes under Setup and architecture, and added daemon launcher to Quick Start.
  - [x] Updated `doc/user/getting-started.md`: documented `pypost` console script launcher and `python -m pypost` alongside `make run`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1269/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1269/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1269/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1269/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1269/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/daemon.md`
- `doc/dev/README.md`
- `doc/user/getting-started.md`
- `ai-tasks/PYPOST-1269/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
