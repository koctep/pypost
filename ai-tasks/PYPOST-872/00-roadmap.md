# Roadmap: PYPOST-872

## Programming Language

Makefile + Python (pytest contract tests under `tests/`); Markdown for
developer docs (`.cursor/lsr/do-python.md`, `do-testing.md`, `do-markdown.md`).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_makefile.py` — `venv-test` on `test` / `test-agent-e2e`
- [x] **STEP 4: Development**
  - [x] ENABLE `venv-test` on `test` / `test-slow` / `test-agent-e2e`
  - [x] Align runtime-target contract test (exclude `test` from no-venv-test)
  - [x] Add `test-slow` dependency-chain assert; Step 3 reds green
  - [x] Replace bare-venv failure smoke with success-via-`venv-test`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/testing.md` — install-first + auto `venv-test` contract
  - [x] `doc/dev/setup.md` — Makefile dependency notes

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-872/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-872/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_makefile.py` (`TestDependencyChain` venv-test asserts)

### STEP 4: Development

- Root `Makefile` (`test` / `test-slow` / `test-agent-e2e` + `venv-test`)
- `tests/test_makefile.py` contract updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-872/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-872/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-872/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
- `doc/dev/setup.md`
