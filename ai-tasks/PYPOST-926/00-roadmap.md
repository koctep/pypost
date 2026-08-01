# Roadmap: PYPOST-926

**Programming language:** Python for `tests/conftest.py` and pytest contract guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_conftest_lazy_qt_import.py` — red on eager conftest import
- [x] **STEP 4: Development**
  - [x] Moved `PySide6.QtWidgets.QApplication` import inside `qapp` fixture
  - [x] Contract + qapp smoke tests green
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

- `ai-tasks/PYPOST-926/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-926/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_conftest_lazy_qt_import.py`

### STEP 4: Development

- `tests/conftest.py`
- `tests/test_conftest_lazy_qt_import.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-926/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-926/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-926/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
