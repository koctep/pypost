# PYPOST-699: Resolve empty utils/ package

## Goals

Close architecture audit finding **R-P3-001 (L-006)** from PYPOST-684: remove the unused
`pypost/utils/` package so the documented directory tree matches the codebase and
developers are not misled by a placeholder package with no shared helpers.

**Business intent:** Reduce architectural noise and documentation drift — no user-visible
behavior change.

## User Stories

- As a **developer**, I want the package tree to list only real modules, so I know where to
  add shared helpers when they are needed.
- As a **reviewer**, I want `architecture_audit.md` to mark L-006 remediated, so the P3
  backlog reflects current state.

## Definition of Done

- `pypost/utils/` removed (empty `__init__.py` and directory).
- No remaining imports of `pypost.utils` in production or tests.
- `doc/dev/architecture.md` directory tree no longer lists `utils/`.
- `doc/dev/architecture_audit.md` marks L-006 and R-P3-001 as remediated.
- `make check` passes.

## Out of scope

- Adding new shared helper modules elsewhere.
- Refactoring existing `scan_utils` or third-party `mcp.shared._httpx_utils` imports.

## Source

- Jira [PYPOST-699](https://pypost.atlassian.net/browse/PYPOST-699)
- Audit L-006 / R-P3-001 in `ai-tasks/PYPOST-684/30-audit-report.md`
