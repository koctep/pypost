# PYPOST-816: Add ai-tasks artifact completeness CI check

## Summary

Follow-up from [PYPOST-772](https://pypost.atlassian.net/browse/PYPOST-772) item **R-P2-006b**.
Add an automated verifier that fails `make check` when a newly closed `ai-tasks/PYPOST-*`
folder is missing required workflow markdown files. Grandfather existing legacy gaps via a
committed baseline snapshot (same pattern as `mypy-baseline.json`).

## Acceptance Criteria

1. `scripts/verify_ai_task_artifacts.py` scans `ai-tasks/` and parses `00-roadmap.md` for
   completed tasks (all seven workflow steps marked `[x]`, including collapsed `STEP 1–7`).
2. Standard closed tasks require the seven-file set documented in `doc/dev/setup.md`.
3. Code Audit tasks PYPOST-684–689 require the eight-file set (`30-audit-report.md` included).
4. `ai-tasks-artifacts-baseline.json` freezes known legacy missing-file gaps; the verifier fails
   only on new or changed violations.
5. `make verify-ai-tasks` runs the script; `make check` includes it after lint and tests.
6. Unit tests cover roadmap parsing, required file sets, violation collection, and baseline parity.
7. `make check` passes.

## Out of Scope

- Backfilling historical thin folders to meet the standard.
- Jira automation or updating closed issues.
- Enforcing supplemental reports (`investigation-report.md`, etc.).

## User Stories

- As a **maintainer**, I want `make check` to catch incomplete closed task folders so new work
  follows the documented top-down workflow artifacts.
- As a **contributor**, I want legacy incomplete folders grandfathered so CI stays green while
  new tasks are held to the documented standard.
