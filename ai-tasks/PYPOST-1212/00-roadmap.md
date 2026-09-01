# Roadmap: PYPOST-1212

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gathered requirements for deterministic repro and baseline evidence for large-batch apply_theme segfault
  - [x] Defined functional and non-functional requirements, scope boundaries, and business entities
  - [x] Created `ai-tasks/PYPOST-1212/10-requirements.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Researched PYPOST-1070 discovery facts, crash surface (`apply_theme`), environment matrix, and batch contrast
  - [x] Evaluated subprocess-based repro harness design options and signal-capturing mechanisms
  - [x] Defined Step 3 failing repro protocol and Step 4 development / evidence baseline plan
  - [x] Designed architecture, Mermaid workflows, and downstream component contracts for DIAG-1 (PYPOST-1213) and MITIGATE-1 (PYPOST-1214)
  - [x] Authored `ai-tasks/PYPOST-1212/20-architecture.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] Created `tests/test_gui_batch_segfault_repro.py` subprocess-based reproduction and baseline verification test
  - [x] Created CLI diagnostic harness in `scripts/repro_gui_batch_segfault.py`
  - [x] Verified bounded batch execution passes cleanly (`test_bounded_gui_batch_execution_passes_cleanly`)
  - [x] Captured large-batch execution under unmitigated single-process conditions with `@pytest.mark.xfail(strict=False, reason="PYPOST-1117: large-batch apply_theme native segfault")` (`test_large_batch_gui_execution_unmitigated_segfault_repro`)
  - [x] Verified execution via Make targets: `make test PYTEST_ARGS="tests/test_gui_batch_segfault_repro.py -v -m slow"` and `make test-slow PYTEST_ARGS="tests/test_gui_batch_segfault_repro.py -v -m 'slow or not slow'"`
  - [x] Red/xfail proof surface path: `tests/test_gui_batch_segfault_repro.py`
  - [x] Review gate passed (PASS)
- [x] **STEP 4: Development**
  - [x] Authored baseline evidence record in `ai-tasks/PYPOST-1212/30-baseline-evidence.md` with environment inventory, reproduction commands, crash forensics, pass/fail contrast table, and downstream contracts
  - [x] Authored developer guide in `doc/dev/gui_batch_segfault.md` covering CLI harness usage, crash signatures, empirical contrast table, and DIAG-1/MITIGATE-1 handoff
  - [x] Cross-linked `doc/dev/gui_batch_segfault.md` in `doc/dev/gui_testing.md` and `doc/dev/README.md`
  - [x] Validated quality gates via `make lint`, `make lint-docs`, `make check-docs-links`, `make verify-ai-tasks`, `make typecheck`, and `make test-slow`
  - [x] Review gate passed (PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] Formatted code and wrapped lines exceeding 100 characters in `scripts/repro_gui_batch_segfault.py` and `tests/test_gui_batch_segfault_repro.py`
  - [x] Verified static analysis, documentation linting, link checking, mypy typechecking, and AI task verification via Make targets
  - [x] Verified explicit test timeout markers (`@pytest.mark.timeout(240)` and pytestmark)
  - [x] Created `ai-tasks/PYPOST-1212/40-code-cleanup.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 6: Observability**
  - [x] Analyzed observability for large-batch GUI repro harness and baseline evidence
  - [x] Documented logging architecture (structured stdout/stderr capture, signal decoding, tail truncation, faulthandler integration)
  - [x] Documented metrics and evidence schema (exit codes, signals, execution duration, batch sizes, pass/fail ratios)
  - [x] Documented structured JSON output contract in `scripts/repro_gui_batch_segfault.py`
  - [x] Authored `ai-tasks/PYPOST-1212/50-observability.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed shortcuts taken, code quality issues, missing tests, and performance concerns
  - [x] Triaged pre-existing test failure in full suite (`tests/test_main_window_alert_reload.py`) as NON-BLOCKER
  - [x] Documented downstream follow-up tasks for DIAG-1 (PYPOST-1213) and MITIGATE-1 (PYPOST-1214) under epic PYPOST-1117
  - [x] Created `ai-tasks/PYPOST-1212/60-tech-debt.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Author and review developer documentation in `doc/dev/gui_batch_segfault.md`
  - [x] Update cross-references in `doc/dev/gui_testing.md` and index in `doc/dev/README.md`
  - [x] Verify documentation linting, link checking, and AI task verification via Make
  - [x] Review gate passed (PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1212/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1212/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)
  - `tests/test_gui_batch_segfault_repro.py`
  - `scripts/repro_gui_batch_segfault.py`

### STEP 4: Development

- `ai-tasks/PYPOST-1212/30-baseline-evidence.md`
- `doc/dev/gui_batch_segfault.md`
- `doc/dev/gui_testing.md` (cross-link update)
- `doc/dev/README.md` (index update)
- `scripts/repro_gui_batch_segfault.py`
- `tests/test_gui_batch_segfault_repro.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1212/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1212/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1212/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/gui_batch_segfault.md`
- `doc/dev/gui_testing.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
