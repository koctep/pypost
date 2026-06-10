# Roadmap: PYPOST-490

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `tests/test_settings_hidden_toggle_logging_e2e.py` with two
        acceptance tests covering default masked and opt-in readable key logging
        through SettingsDialog → MainWindow.apply_settings →
        EnvPresenter._open_env_manager → hidden toggle → caplog; all 65 related
        tests pass; no production wiring defects found.
- [x] **STEP 4: Code Cleanup**
  - [x] Linted and formatted `tests/test_settings_hidden_toggle_logging_e2e.py`; flake8
        and line-length checks pass; 2 new tests and 75 PYPOST-448-related tests pass;
        documented in `40-code-cleanup.md`.
- [x] **STEP 5: Observability**
  - [x] Documented existing `env_hidden_flag_changed` INFO event and PYPOST-448 policy wiring in
        `50-observability.md`; confirmed no new production logs or metrics required for this
        test-debt task; integration test assertions mapped to observability validation.
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.10+ (same as the pypost application codebase; see `.cursor/lsr/do-python.md`).

## Related Work

- Parent feature: [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448) (configurable
  hidden-key name logging)
- Source debt item: [PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md)
- Related, separate coverage: [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489)
  (environment persistence e2e with default masked logging)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-490/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-490/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-490/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-490/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-490/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-490/70-dev-docs.md`
- `doc/dev/hidden_variables.md` (Related Tests entry)

## Task Context

- Programming language: Python
- Jira issue: PYPOST-490
- Summary: Integration test for settings-to-masked hidden-toggle logging flow
- Type: Debt (test coverage)
- Recommended branch name: `test/PYPOST-490-settings-hidden-toggle-logging-e2e`
