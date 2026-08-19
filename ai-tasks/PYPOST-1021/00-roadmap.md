# Roadmap: PYPOST-1021

## Task Metadata

- **Implementation language**: Python / Makefile / YAML
- **Branch name**: feature/PYPOST-1021-doc-user-relative-links

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for relative link and anchor validation across User Guide, `doc/README.md`, and root `README.md`
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1021/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design relative link checker script `scripts/check_user_docs_links.py`, test suite `tests/test_doc_user_relative_links.py`, and Makefile / CI integration
  - [x] Produce architecture artifact `ai-tasks/PYPOST-1021/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Added `tests/test_doc_user_relative_links.py` with synthetic broken target/anchor detection test
- [x] **STEP 4: Development**
  - [x] Created `scripts/check_user_docs_links.py`
  - [x] Added `check-docs-links` target in `Makefile` and wired into `make lint` and CI `test.yml`
  - [x] Verified all tests pass 100% GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint`, `make check-mcp-fixtures`, `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-1021/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify checker output and error diagnostics
  - [x] Produce `ai-tasks/PYPOST-1021/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status (including examples/README.md in relative link checker in PYPOST-1031)
  - [x] Produce `ai-tasks/PYPOST-1021/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Check testing and linting documentation
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-1021/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-1021/20-architecture.md`

### STEP 3: Failing Repro Test
- `tests/test_doc_user_relative_links.py`

### STEP 4: Development
- `scripts/check_user_docs_links.py`
- `Makefile`
- `.github/workflows/test.yml`
- `tests/test_doc_user_relative_links.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-1021/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-1021/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-1021/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
