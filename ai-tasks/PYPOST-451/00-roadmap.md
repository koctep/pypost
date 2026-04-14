# Roadmap: PYPOST-451

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pypost/core/function_registry.py` with `FunctionRegistry` (catalog,
        `allowed_names`, `is_allowed`, `get`, `register_into_env`) and moved
        urlencode/md5/base64 implementations into the module.
  - [x] Refactored `TemplateService` to use `FunctionRegistry` for Jinja globals and
        validation; removed duplicated allow-list and static helpers.
  - [x] Added `tests/test_function_registry.py`; `tests/test_template_service.py`
        unchanged behavior; ran `scripts/lint.sh`, `scripts/test.sh`, and
        `scripts/check-line-length.sh` on changed files and roadmap.
  - [x] Test review fixes: public `urlencode` assertion; `unknown_function` name parity.
- [x] **STEP 4: Code Cleanup**
  - [x] Scoped `scripts/lint.sh` clean; `scripts/check-line-length.sh` on
        scoped files; PEP 8 import grouping in `tests/test_template_service.py`;
        `scripts/test.sh` all green; `40-code-cleanup.md` recorded.
- [x] **STEP 5: Observability**
  - [x] Gap analysis: no new critical path beyond existing `TemplateService` logs
        and metrics; `FunctionRegistry` intentionally without logging.
  - [x] Documented existing pipeline in `ai-tasks/PYPOST-451/50-observability.md`
        (no code changes in STEP 5).
  - [x] Validation: `scripts/test.sh` (green); `scripts/check-line-length.sh` on
        `50-observability.md` and `00-roadmap.md` (green); `scripts/lint.sh` on
        related Python modules (`template_service.py`, `function_registry.py`,
        `metrics.py`, `test_template_service.py`) — no STEP 5 Python edits.
- [x] **STEP 6: Review and Technical Debt**
  - `ai-tasks/PYPOST-451/60-tech-debt.md` completed; user-approved; follow-up Jira
    PYPOST-456–458 created (links in debt file).
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/template_expression_functions.md` for `FunctionRegistry` (PYPOST-451);
        addresses roadmap reminder and [PYPOST-456](https://pypost.atlassian.net/browse/PYPOST-456).

## Programming language

Python (project standard for this codebase).

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-451/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-451/20-architecture.md` (user-approved)

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-451/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-451/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-451/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/template_expression_functions.md` (updated for PYPOST-451 / `FunctionRegistry`)
