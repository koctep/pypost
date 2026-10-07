# PYPOST-1266: Observability Implementation

## Observability Requirements Analysis

The typed reader contract changes how the existing background worker invokes its dependency.
The critical paths remain parse completion, cooperative cancellation, file failure, and an
unexpected reader exception. The accepted architecture keeps the same signals, state machine,
and safe checkpoints, so no new runtime component or telemetry boundary needs instrumentation.

Existing outcome logs and metrics are sufficient for this scope. No production logging,
metrics, exporter configuration, or dashboards were added. Per-record logging would add volume
without proving cancellation support; the protocol and deterministic contract tests establish
that guarantee. Whole-file decoding latency remains outside this issue under PYPOST-1267.

## Logging Implementation

### Retained Worker Logs

`pypost/core/qt/collection_import_parse_worker.py` retains these event prefixes:

- **DEBUG**: `collection_import_parse_worker_started` includes `path`.
- **DEBUG**: `collection_import_parse_worker_completed` includes `path`, candidate `count`, and
  `error_count`; it does not serialize candidates or per-record errors.
- **INFO**: `collection_import_parse_worker_cancelled` includes `path`. Checkpoint exceptions
  unwind into this branch and emit `parse_cancelled`, without a failure log.
- **WARNING**: `collection_import_parse_worker_failed` includes `path` and `reason` for a
  `CollectionImportFileError`.
- **ERROR**: `collection_import_parse_worker_failed` includes `path`, exception text in `error`,
  and traceback context for an unexpected exception. An unsupported single-argument reader now
  reaches this existing branch with `TypeError`, rather than silently bypassing checkpoints.

### Retained Action and Lifecycle Logs

`pypost/ui/presenters/collection_import_actions.py` retains:

- **INFO**: parse start with `path`, cancellation with `from_state`, and import completion
  with aggregate added, updated, skipped, renamed, request, and error counts.
- **DEBUG**: state transitions with `from` and `to`, plus busy-cue and worker-reaping events.
- **INFO/WARNING**: bounded wait and teardown diagnostics, including `elapsed_ms`, `timeout_ms`,
  interruption outcomes, and the final teardown `clean` flag.
- **WARNING/ERROR**: expected invalid-file and unexpected parse outcomes, respectively.

### Log Structure

The existing Python loggers emit stable event prefixes with scalar `key=value` context. These
are structured message conventions, not a new JSON formatter. Levels remain DEBUG, INFO,
WARNING, and ERROR. This issue adds no payload, record, collection, or callback dumps; existing
path and exception context is retained. No logging is added inside the checkpoint callback.

## Metrics Implementation

`CollectionImportActions._track_import_event()` already calls
`MetricsTrackerProtocol.track_gui_library_operation()` with
`operation="collection_import_file"`. File import records `started`, then the existing outcome:

- `success` or `failure` after application;
- `failure` for empty candidates or a parse exception;
- `rejected` for picker abandonment or cooperative cancellation.

Cancellation therefore remains observable without being counted as a parse failure. The
`rejected` outcome also covers picker abandonment and is not a dedicated cancellation count.
The protocol change does not alter this meaning or introduce reader/path labels.

The existing Prometheus registry and OpenTelemetry implementation both expose
`gui_library_operations_total` with bounded `operation` and `outcome` dimensions. The optional
metrics dependency still resolves to a no-op tracker when absent. No new duration, throughput,
resource, or cancellation-latency metric is necessary to validate this dependency contract;
existing wait diagnostics report elapsed time when lifecycle waits occur.

## Monitoring Integration

Existing metrics backends and logging configuration remain the integration points. This issue
requires no additional Prometheus exporter, OpenTelemetry instrument, alert, or dashboard.
No new monitoring endpoint was introduced or exercised during this step.

## Validation Results

- Source inspection confirmed that all worker outcomes retain their existing log branches and
  that cooperative cancellation remains separate from failure handling.
- Source inspection confirmed the bounded metric dimensions and unchanged cancellation outcome
  in the action layer; this step does not claim a new live exporter or scrape validation.
- `make test` passed four selected tests across three modules with `WORKERS=1` and
  `WORKER_TIMEOUT=60`: legacy-reader ERROR logging in
  `tests/test_collection_import_progress.py`, cooperative cancellation/state logging in
  `tests/test_collection_import_cancellation_repro.py`, and wait completion/timeout logging in
  `tests/test_collections_import_ui_repro.py`. No test or production changes were needed.
- `make lint-docs verify-ai-tasks` passed: user-document lint checked 16 files, relative-link
  checks covered 18 files, and task integrity accepted 391 completed tasks with two existing
  grandfathered legacy gaps. The documentation targets cover user docs; this task report was
  reviewed directly for accurate source references and Markdown structure.

## Notes

This step changes task documentation only. Step 4 already passed the supported-reader shape,
production JSON, progress, cancellation, responsiveness, and UI contract checks. Step 5's full
quality-gate failures were classified separately; this step does not reopen that triage or
change the accepted production implementation.
