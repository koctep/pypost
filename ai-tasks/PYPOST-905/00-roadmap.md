# Roadmap: PYPOST-905

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *`tests/test_makefile.py` — `TestVenvExtraStampIdempotency` (skip when current; install when missing/stale; stamp prereqs)*
- [x] **STEP 4: Development**
  - [x] *Option B stamp files for `venv-test` / `venv-otel`; `install` touches both*
  - [x] *Updated marker→stamp contract asserts; Step 3 red tests green*
- [x] **STEP 5: Code Cleanup**
  - [x] *`40-code-cleanup.md`; lint + `test_makefile.py` (48 passed)*
- [x] **STEP 6: Observability**
  - [x] *`50-observability.md` — N/A app logs; Make skip/install visibility*
- [x] **STEP 7: Review and Technical Debt**
  - [x] *`60-tech-debt.md` — SAFE TO CLOSE; Low: install-touches-stamps test*
- [x] **STEP 8: Dev Docs**
  - [x] *`doc/dev/testing.md` + `setup.md` stamp wording; `70-dev-docs.md`*

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Makefile (root build interface) with Python pytest contract / smoke tests
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-905/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-905/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_makefile.py` — `TestVenvExtraStampIdempotency`
  (skip-when-current red; install-when-needed; stamp prereq asserts)

### STEP 4: Development

- Root `Makefile` — Option B stamps + `install` touch
- `tests/test_makefile.py` — green skip / install / stamp contracts

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-905/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-905/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-905/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`, `doc/dev/setup.md`
- `ai-tasks/PYPOST-905/70-dev-docs.md`
