# Roadmap: PYPOST-865

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_pytest_strict_markers.py` —
    `test_addopts_includes_strict_markers`
    (Step 3: red assert; Step 4: enable flag)
- [x] **STEP 4: Development**
  - [x] Verified `--strict-markers` in `pyproject.toml` `addopts`
  - [x] Verified markers registry: `timeout`, `slow`, `agent_e2e`
  - [x] Guard tests green: flag + required markers registered
  - [x] Collection smoke: no unknown-marker usage errors
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Programming language

Python 3.11+ (`.cursor/lsr/do-python.md`) for the pytest config guard.
Markdown under `doc/dev/` follows `.cursor/lsr/do-markdown.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-865/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-865/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pytest_strict_markers.py` —
  `test_addopts_includes_strict_markers`

### STEP 4: Development

- `pyproject.toml` — `--strict-markers` in `addopts`
- `tests/test_pytest_strict_markers.py` — flag + marker registry guards
- Source / config changes

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-865/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-865/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-865/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
- `ai-tasks/PYPOST-865/70-dev-docs.md`

## Suggested branch name

`test/PYPOST-865-strict-markers`

## Decision

**ENABLE** `--strict-markers` in `[tool.pytest.ini_options]` `addopts`
(not defer). Suite audit shows only registered custom marks
(`timeout`, `slow`, `agent_e2e`) plus builtins.
