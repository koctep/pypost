# Roadmap: PYPOST-922

**Programming language:** Python (docs Markdown; Makefile packaging entry)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_makefile.py` (help + default recipe broader-than-golden)
  - [x] `tests/test_agent_e2e_broader_packaging_doc.py` (doc-token lock)
- [x] **STEP 4: Development**
  - [x] Updated `Makefile` `##` help for `test-agent-e2e` to frame broader
    pack beyond golden (reuse same target / recipe)
  - [x] Aligned `doc/dev/agent_e2e.md`, `agent_golden_e2e.md`, and
    `testing.md` (primary packaging vs golden `PYTEST_ARGS` narrow;
    PYPOST-922 attribution)
  - [x] Contract tests green (makefile help/recipe + packaging doc tokens)
- [x] **STEP 5: Code Cleanup**
  - [x] flake8 E203 fix in `test_makefile.py` slice; flake8 clean on
    touched tests
  - [x] Targeted contract tests green (9 passed); timeouts present
  - [x] `40-code-cleanup.md` created
- [x] **STEP 6: Observability**
  - [x] N/A for runtime logging/metrics (docs/make discoverability);
    `50-observability.md` documents decision
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` with unticketed follow-ups (no Jira creates)
- [x] **STEP 8: Dev Docs**
  - [x] Sibling discoverability: `setup.md`, `gui_testing.md`,
    `agent_lifecycle.md`, `agent_e2e_env.md`, `doc/dev/README.md`
    aligned with broader-beyond-golden primary packaging (PYPOST-922)
  - [x] Primary locks already in `agent_e2e.md` / `agent_golden_e2e.md` /
    `testing.md` (Step 4)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-922/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-922/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (makefile help/recipe + packaging
  doc tokens; see `20-architecture.md` Failing Repro)
- `tests/test_makefile.py` — `TestAgentE2eTargetRecipe` /
  `TestHelpTarget` broader-beyond-golden locks (PYPOST-922)
- `tests/test_agent_e2e_broader_packaging_doc.py` — doc-token lock
  (PYPOST-922 attribution + primary vs golden `PYTEST_ARGS` narrow)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-922/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-922/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-922/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/` (primary: `agent_e2e.md`, `agent_golden_e2e.md`, `testing.md`;
  sibling soft-wording: `setup.md`, `gui_testing.md`, `agent_lifecycle.md`,
  `agent_e2e_env.md`, `doc/dev/README.md`)
