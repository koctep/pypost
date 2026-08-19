# Roadmap: PYPOST-1020

## Task Metadata

- **Implementation language**: Python / Makefile / YAML
- **Branch name**: feature/PYPOST-1020-doc-user-markdown-lint

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for User Guide Markdown linting (line length <= 100, trailing whitespace, ATX headers, bullet list consistency)
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1020/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design standalone linter script `scripts/lint_user_docs.py`, automated contract tests `tests/test_doc_user_markdown_lint.py`, and Makefile / CI integration
  - [x] Produce architecture artifact `ai-tasks/PYPOST-1020/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Added `tests/test_doc_user_markdown_lint.py`
  - [x] Verified linter catches line length violation in `doc/user/environments.md:76`
- [x] **STEP 4: Development**
  - [x] Created `scripts/lint_user_docs.py`
  - [x] Fixed line 76 in `doc/user/environments.md`
  - [x] Added `lint-docs` target in `Makefile` and wired into `make lint` and CI `test.yml`
  - [x] Verified all tests pass 100% GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint`, `make check-mcp-fixtures`, `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-1020/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify linter output and test failure diagnostics
  - [x] Produce `ai-tasks/PYPOST-1020/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status (relative link checker follow-up in PYPOST-1021)
  - [x] Produce `ai-tasks/PYPOST-1020/60-tech-debt.md`
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
- `ai-tasks/PYPOST-1020/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-1020/20-architecture.md`

### STEP 3: Failing Repro Test
- `tests/test_doc_user_markdown_lint.py`

### STEP 4: Development
- `scripts/lint_user_docs.py`
- `doc/user/environments.md`
- `Makefile`
- `.github/workflows/test.yml`
- `tests/test_doc_user_markdown_lint.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-1020/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-1020/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-1020/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
