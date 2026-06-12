# PYPOST-429: Observability

## Scope

Investigation task. No logging, metrics, or tracing changes.

## Existing coverage

- `TabsPresenter._on_request_error` already logs `request_error` at ERROR level (visible in
  pytest live log during `TestOnRequestError` runs).
- No core-dump or crash telemetry exists — native segfaults terminate the process before Python
  logging can flush.

## Result

Not applicable — investigation documented manual lldb steps in `investigation-report.md` §5.
