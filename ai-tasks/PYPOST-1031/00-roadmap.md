# Roadmap: PYPOST-1031

## Task Metadata

- **Implementation language**: Python / English Markdown
- **Branch name**: feature/PYPOST-1031-link-checker-examples-readme

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for including `examples/README.md` in `scripts/check_user_docs_links.py` and `tests/test_doc_user_relative_links.py`
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1031/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design multi-directory relative link checker target registration
  - [x] Produce architecture artifact `ai-tasks/PYPOST-1031/20-architecture.md`
- [x] **STEP 3: Failing Repro Test / Verification Baseline**
  - [x] Confirmed `examples/README.md` was excluded from default targets
- [x] **STEP 4: Development**
  - [x] Added `examples/README.md` to `scripts/check_user_docs_links.py`
  - [x] Added `examples/README.md` to `tests/test_doc_user_relative_links.py`
  - [x] Verified all 18 test cases pass 100% GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint`, `make check-mcp-fixtures`, `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-1031/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify link checker output count
  - [x] Produce `ai-tasks/PYPOST-1031/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status
  - [x] Produce `ai-tasks/PYPOST-1031/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Verified link verification gates
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-1031/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-1031/20-architecture.md`

### STEP 4: Development
- `scripts/check_user_docs_links.py`
- `tests/test_doc_user_relative_links.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-1031/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-1031/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-1031/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
