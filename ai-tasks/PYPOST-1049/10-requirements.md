# PYPOST-1049: Clear verify-ai-tasks baseline drift for missing 70-dev-docs.md

## Programming Language

Python and JSON for baseline artifact verification, English Markdown for documentation.

## Goals

Follow-up from PYPOST-1047 (TD-3). In older sprints, tasks completed under earlier standards were missing `70-dev-docs.md`, creating potential baseline drift in `scripts/verify_ai_task_artifacts.py`.

**Business goal:** Validate that `verify_ai_task_artifacts.py` and `ai-tasks-artifacts-baseline.json` accurately account for all completed tasks without baseline drift, ensuring `make verify-ai-tasks` and `make check` remain completely green.

## Definition of Done

- [ ] All completed tasks in `ai-tasks/` comply with the current artifact specification or grandfathered baseline.
- [ ] `make verify-ai-tasks` exits 0 with zero drift.
- [ ] `tests/test_verify_ai_task_artifacts.py` passes all 19 contract tests.
