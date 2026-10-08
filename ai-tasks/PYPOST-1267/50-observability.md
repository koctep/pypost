# PYPOST-1267: Observability Implementation

## Logging Implementation

### Existing Logs Reused

No new production logs are necessary. Loading and decoding now unwind through the existing
worker lifecycle, which already distinguishes cancellation from failure and successful parsing.

- **DEBUG**: `pypost/core/qt/collection_import_parse_worker.py` emits
  `collection_import_parse_worker_started` with the selected path, and
  `collection_import_parse_worker_completed` with path, candidate count, and error count.
- **INFO**: the same worker emits `collection_import_parse_worker_cancelled` with path when
  interruption stops reading, JSON decoding, YAML decoding, or record validation. Cancellation
  emits its dedicated signal and bypasses the warning/error handlers.
- **INFO**: `pypost/core/collection_import.py` emits `collection_import_file_parsed` with path,
  candidate count, and validation-error count after successful reader completion.
- **WARNING**: the reader retains `collection_import_file_read_failed` and
  `collection_import_parse_failed` for ordinary file/format errors. The worker emits
  `collection_import_parse_worker_failed` for `CollectionImportFileError`.
- **ERROR**: the worker retains `collection_import_parse_worker_failed` with exception context
  for unexpected reader exceptions. Callback-origin exceptions preserve their original identity;
  cancellation is never translated into a file or format failure.
- **INFO**: `pypost/ui/presenters/collection_import_actions.py` retains
  `collection_import_parse_started` and `collection_import_parse_cancelled from_state=...`.
  Existing teardown events report interruption, timeout, and cleanup outcomes.

### Log Structure and Privacy

Existing messages use stable event names followed by key/value context through Python logging.
They use DEBUG, INFO, WARNING, and ERROR levels and retain the repository logging configuration.
No checkpoint, read-chunk, scalar, token, alias, or collection contents are newly logged.
The decoding helper has no logger; its frequent checkpoints only invoke the existing callback.
Preparation `(0, 0)` callbacks produce neither GUI progress nor log entries in the worker.
Existing exception diagnostics remain unchanged; this step does not claim that pre-existing
parser exception messages exclude excerpts of malformed input.

## Metrics Implementation

### Existing Lifecycle Counter Reused

The presenter already calls `track_gui_library_operation()` with the bounded operation
`collection_import_file`. Its outcomes are `started`, `success`, `failure`, and `rejected`;
`_on_parse_cancelled()` records `rejected`, including cancellation during the new preparation
checkpoints. This counter describes lifecycle events, not bytes or records processed.

`pypost/core/metrics_registry.py` exposes these events through the Prometheus counter
`gui_library_operations_total`, with normalized `operation` and `outcome` labels.
`pypost/core/metrics_otel.py` exposes the same counter through OpenTelemetry. Labels contain no
file paths, imported data, or exception strings. Metrics remain optional through the existing
metrics protocol and resolver; this task introduces no backend configuration or dashboards.

### Performance and System Metrics

No new production histogram or resource metric is necessary for this cooperative cancellation
change. The accepted responsiveness target is measured from request to worker stop in the
real-file regression tests. Those tests record `cancellation_latency_ms`, `latency_limit_ms`,
`fixture_bytes`, `phase`, `format`, and `shape` as test properties. They do not establish a
production latency distribution. Step 4 recorded the measured results in the roadmap.

Per-checkpoint instrumentation would add work to the critical cancellation path without a new
operational requirement. CPU, memory, throughput guarantees, and monitoring deployment changes
remain outside the accepted requirements.

## Validation Results

Focused verification reused existing cancellation and unexpected-error logging assertions:

```bash
make test WORKERS=1 WORKER_TIMEOUT=180 \
  PYTEST_ARGS='tests/test_collection_import_cancellation_repro.py
  tests/test_collection_import_async_gaps.py tests/test_collection_import_progress.py'
```

All three modules passed, exit 0, in 4.25 seconds:

- Cancellation coverage checks prompt worker termination, exactly one cancellation outcome,
  discarded results, and the presenter cancellation/interruption diagnostic events.
- Async-gap coverage captures unexpected reader ERROR logs and verifies the failure dialog.
- Progress coverage captures the worker ERROR event for an unsupported legacy reader and
  verifies the expected failure without completion or cancellation signals.

Source inspection confirms that ordinary file failures retain WARNING diagnostics, helper
checkpoints contain no logging/metrics, and lifecycle metric labels remain bounded. Production
logs, metrics, and tests were not changed during this step. No broad suite rerun was necessary;
the accepted Step 5 cleanup report retains the full-suite and unchanged-rerun evidence.
`make lint` also passed: production flake8, Markdown lint (16 files), and relative links
(18 files). The lint target's existing document selection is unchanged.

## Acceptance

Step 6 remains `[/]` pending independent review by the autonomous orchestrator.
