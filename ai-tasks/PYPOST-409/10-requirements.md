# PYPOST-409: Remove redundant `script_error` field from ExecutionResult

## Goals

PYPOST-400 introduced structured `ExecutionError` on `ExecutionResult` while keeping the legacy
`script_error: Optional[str]` field for backward compatibility. Both fields carried the same
content for post-script failures, creating a dual source of truth that increases maintenance
risk and confuses callers. This task eliminates the redundancy so script failures have a single
canonical representation.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want script failures represented only via `execution_error` so callers
  do not need to check two fields for the same condition.
- As a developer extending request execution, I want a clear contract: post-script errors use
  `ErrorCategory.SCRIPT` with the raw exception string in `detail`.

## Definition of Done

- `ExecutionResult` no longer exposes a `script_error` field.
- `RequestService.execute()` still returns a result (not raises) when post-scripts fail, with
  `execution_error.category == ErrorCategory.SCRIPT`.
- `RequestWorker` emits script output using `execution_error.detail` for script failures.
- `MCPServerImpl` appends script error sections from `execution_error` when category is SCRIPT.
- All affected unit tests pass without asserting on `script_error`.
- Developer documentation reflects the single-field contract.

## Task Description

Follow-up to PYPOST-400 tech debt item TD-1. Scope is limited to removing the redundant string
field and migrating in-repo callers. No change to UI messaging, metrics labels, or
`ScriptExecutor` return type.

### Out of scope

- Template render guard / double-render (PYPOST-410).
- MCP heuristic error classification (PYPOST-411).
- Worker `ExecutionError` handler test coverage (PYPOST-412).
- Cancellation category (PYPOST-413).

## Q&A

- **Why not deprecate with a warning first?** In-repo callers are few and fully controlled;
  removal in one sprint avoids prolonged dual-field drift.
- **Where is the script error string now?** `ExecutionResult.execution_error.detail` when
  `category == ErrorCategory.SCRIPT`.
