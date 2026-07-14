# PYPOST-740: Clarify request_sync Module Naming

> Parent: [PYPOST-687](https://pypost.atlassian.net/browse/PYPOST-687) R-P3-004

## Summary

Rename `pypost/core/request_sync.py` to a name that reflects its purpose — persisted-field
copy and comparison helpers for tab isolation — not HTTP request synchronization.

## User Stories

- As a **contributor**, I want module names to match their behavior, so I do not confuse tab
  dirty helpers with MCP/HTTP sync paths.
- As a **reviewer**, I want imports to read clearly at call sites.

## Acceptance Criteria

- [x] Module renamed to `request_persisted_fields.py`.
- [x] All production and test import sites updated (~8).
- [x] Test module renamed to `test_request_persisted_fields.py`.
- [x] Active `doc/dev/` references updated.
- [x] `make check` passes.
- [x] No behavior change — rename only.

## Out of Scope

- Renaming `MCPServerImpl._execute_request_sync` (unrelated MCP execution path).
- Moving helpers out of `core/` (addressed separately in PYPOST-696 for `is_tab_dirty`).

## Constraints

- Mechanical rename; preserve public API function names.
