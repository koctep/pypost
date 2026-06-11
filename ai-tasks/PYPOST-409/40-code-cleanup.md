# PYPOST-409: Code Cleanup

## Changes

- Removed `script_error` field from `ExecutionResult` dataclass — eliminates dual
  source of truth with `execution_error`.
- Kept local `script_error` variable in `RequestService.execute()` only as the return value
  from `ScriptExecutor.execute()` before wrapping into `ExecutionError`; not stored on result.
- Migrated `RequestWorker.run()` and `MCPServerImpl.call_tool()` to read script failures from
  `execution_error` with an explicit `ErrorCategory.SCRIPT` check.
- Updated test helpers and assertions to construct/check `execution_error` instead of
  `script_error`.

## No further cleanup required

- No dead imports introduced.
- No duplicated script-error extraction helper added (two call sites; inline check is clear).
- `tabs_presenter` log message key `script_error` retained — refers to log field name, not
  dataclass field.
