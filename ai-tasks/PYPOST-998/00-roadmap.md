# Roadmap: PYPOST-998

## Task Metadata

- **Implementation language**: Makefile / English Markdown
- **Branch name**: feature/PYPOST-998-check-lock-docs-target

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for documenting `make check` vs `make check-lock` / `check-lock-all` and adding convenience target
  - [x] Produce requirements artifact `ai-tasks/PYPOST-998/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design clear boundary between fast offline gates (`make check`) and lock compiler checks (`make check-lock-all`)
  - [x] Produce architecture artifact `ai-tasks/PYPOST-998/20-architecture.md`
- [x] **STEP 3: Failing Repro Test / Verification Baseline**
  - [x] Verified `doc/dev/setup.md` lacked explicit distinction and step-by-step workflow
- [x] **STEP 4: Development**
  - [x] Added `check-lock-all` target in `Makefile`
  - [x] Documented "Lock verification and quality gates (PYPOST-998)" in `doc/dev/setup.md`
  - [x] Verified all quality targets and test suites pass 100% GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint`, `make check-mcp-fixtures`, `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-998/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify Makefile help output and documentation formatting
  - [x] Produce `ai-tasks/PYPOST-998/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status
  - [x] Produce `ai-tasks/PYPOST-998/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/setup.md`
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-998/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-998/20-architecture.md`

### STEP 4: Development
- `Makefile`
- `doc/dev/setup.md`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-998/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-998/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-998/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
