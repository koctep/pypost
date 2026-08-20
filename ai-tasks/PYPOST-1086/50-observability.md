# PYPOST-1086: Observability Assessment

## Decision

No additional production logging or metrics are required in Step 6. The Step 4 implementation
already added the two boundary warnings needed for invalid dynamic payloads, and the existing
request execution and presenter paths already expose failures and useful lifecycle outcomes.
Adding success counters or another thread-finished log would duplicate existing request metrics
and produce noise without improving diagnosis of the type-contract correction.

## Boundary Events

- `env_keys_update_ignored` is a WARNING with `reason` and `type`; it rejects a value other
  than `list` or `None`.
- `script_output_ignored` is a WARNING with `reason` and `type`; it rejects an error detail other
  than `str` or `None`.
- `save_request_overwrite_failed` is an ERROR with `reason` and `request_id`; it stops an invalid
  overwrite result lacking its snapshot.

The rejection warnings are actionable because they identify the violated boundary and unexpected
runtime type. They intentionally omit the rejected object, its string representation, list
contents, environment keys, script error text, and other payload values.

## Existing Error and Lifecycle Behavior

- `RequestWorker` continues to emit its existing `error` signal for cancellation and unexpected
  execution exceptions. Unexpected exceptions retain the existing ERROR log and are converted to
  `ExecutionError` for the presenter.
- The presenter continues to report request errors through its existing ERROR events and user
  notification flow. Request-service metrics already track categorized execution failures through
  `request_errors_total`.
- A successful response continues through `request_finished(ResponseData)`. The presenter already
  emits the existing `request_finished` INFO event with method, status, elapsed time, and size.
- Native `QThread.finished()` remains a cleanup-only lifecycle signal. No new success or cleanup
  log was added because normal thread termination is expected and would duplicate response logs.
- Existing DEBUG worker start, completion, and cancellation events remain unchanged.

## Metrics Decision

New metrics are N/A. The task changes Python and Qt type contracts rather than request throughput,
latency, or business outcomes. Existing request, response, and categorized-error metrics continue
to cover operational behavior. Counting invalid in-process signal payload types is not justified
for these invariant violations; the structured warnings provide sufficient diagnostics without a
new metric family or alerting contract.

## Privacy and Sensitive Data

- Invalid dynamic payload warnings record only `type(value).__name__`; they do not interpolate the
  payload or call `str()` or `repr()` on it.
- Tests use secret-like rejected values and assert that those values are absent from captured logs.
- No environment values, hidden-key values, request or response bodies, script payload contents,
  or collection contents were added to logs.
- The overwrite invariant event includes an existing request identifier for correlation, not the
  request snapshot or body.

## Validation

The exact warning, error-signal, and lifecycle nodes are run through the Makefile, followed by the
worker and presenter-focused modules. `make lint`, `make typecheck`, and `git diff --check` verify
formatting and static integrity. No full-suite rerun is required because Step 6 changes only test
assertions and documentation; Step 4 already completed and base-triaged the full suite.

Results:

- Exact environment warning, script warning, worker error-signal, and lifecycle nodes: 4 passed.
- `tests/test_worker.py`, `tests/test_tabs_presenter.py`, and
  `tests/test_tabs_presenter_on_request_error.py`: 83 passed.
- `make lint`: passed production flake8, Markdown lint, and relative-link checks.
- `make typecheck`: passed with 217 current diagnostics matching 217 baseline records.
- `git diff --check`, trailing-whitespace scan, and 100-character line scan: passed.
