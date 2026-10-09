# PYPOST-1265: Observability Implementation

## Scope

**N/A: no new production observability.** PYPOST-1265 only adds test coverage for
`CollectionImportWorker` cancellation. `git diff -- pypost` is empty. Only
`tests/test_collection_import_cancellation_repro.py` and
`tests/test_collection_import_reader_contract.py` change. `10-requirements.md` (Scope,
"Out of scope") excludes production code changes unless a new regression proves a
defect. Steps 3 and 4 found no such defect. Adding log or metric calls would therefore
widen the scope beyond the accepted requirements. This step only inventories the
existing events on the covered paths and records which ones the new tests assert.

## Logging Implementation

### Added Logs

No new log statements were added (test-only task).

### Existing Events on the Covered Cancellation Paths (unchanged)

Worker logger `pypost.core.qt.collection_import_parse_worker`
(`pypost/core/qt/collection_import_parse_worker.py`, `run()`):

| Event | Level | Fields | Emitted on |
| --- | --- | --- | --- |
| `collection_import_parse_worker_started` | DEBUG | `path` | every run, before the pre-read check |
| `collection_import_parse_worker_cancelled` | INFO | `path` | single `except CollectionImportCancelled` handler, used by all three checkpoints: pre-read, record (`_emit_progress`, including the `(0, 0)` load/decode probe), and post-read final guard |
| `collection_import_parse_worker_completed` | DEBUG | `path`, `count`, `error_count` | normal completion only (must be absent on cancellation) |

Presenter logger `pypost.ui.presenters.collection_import_actions`
(`pypost/ui/presenters/collection_import_actions.py`):

| Event | Level | Fields | Emitted on |
| --- | --- | --- | --- |
| `collection_import_parse_cancelled` | INFO | `from_state` | `_on_parse_cancelled` (GUI terminal event for every worker cancellation; also records metric outcome `rejected`) |
| `collection_import_teardown_started` | INFO | `timeout_ms` | `teardown()` entry |
| `collection_import_worker_interrupting` | WARNING | none | `teardown()` requests interruption (initial request or final join) |
| `collection_import_wait_idle_started` / `_completed` | INFO | `elapsed_ms` (completed) | teardown wait-idle phase |
| `collection_import_wait_idle_timeout` | WARNING | `elapsed_ms` | wait-idle deadline expired |
| `collection_import_worker_interrupted` | INFO | none | worker stopped after interruption (final join succeeded, or reaped during wait-idle) |
| `collection_import_worker_interrupt_timeout` | WARNING | `wait_ms`, `elapsed_ms` | final join timed out (worker ignored the interruption) |
| `collection_import_worker_reaped` | DEBUG | none | worker reference released |
| `collection_import_worker_finish_wait_timeout` | WARNING | `wait_ms` | nested `_on_worker_finished` join overrun |

### Assertions in the New and Changed Tests

| Path | Test | Log assertions |
| --- | --- | --- |
| Pre-start (worker) | `test_worker_pre_start_interruption_skips_reader` | exactly one `collection_import_parse_worker_cancelled` record on the worker logger |
| Pre-start (teardown) | `test_teardown_pre_start_interruption_applies_nothing` | none. It checks signal outcomes and side effects only |
| Record checkpoint (worker) | `test_worker_stops_promptly_when_interrupted_mid_parse` | none. It checks outcome counts and `processed == [1, 2]` |
| Record checkpoint (real YAML) | `test_production_yaml_reader_contract[None/1/2]` | none. It checks the outcome contract only |
| Teardown, explicit budget | `test_teardown_worker_stops_after_interruption` | `collection_import_worker_interrupted` present; exactly one `collection_import_parse_cancelled from_state=parsing`; no `collection_import_worker_interrupt_timeout` |
| Teardown, default budget | `test_default_teardown_requests_interruption_before_wait_and_discards_result` | none. It checks outcomes and that the result dialog is not called |

Behavioural assertions (outcome counts, reader calls, side effects) are the primary
proof, as required by `10-requirements.md` ("Flag-only or log-only checks are not
enough"). The log assertions above are supplementary contracts on events that already
exist. No test reads `caplog` for an error path, so the do-testing caplog
contract (C1-C5) adds nothing new here.

### Log Structure

- Structured logs: yes, existing `event_name key=value` format (unchanged)
- Includes context: yes (`path`, `from_state`, `timeout_ms`, `elapsed_ms`, `wait_ms`)
- Log levels: none added. Existing levels on these paths are DEBUG, INFO and WARNING
- Large data structures: none logged (paths, counts and enum values only)

## Metrics Implementation (if applicable)

### Performance Metrics

N/A. No new metrics in a test-only change. Teardown timing is already logged through
`elapsed_ms` on the wait-idle and interrupt events.

### Business Metrics

N/A. The existing `_track_import_event("collection_import_file", "rejected")` in
`_on_parse_cancelled` is unchanged. None of the new tests assert it.

### System Health Metrics

N/A. Desktop application with no resource or health metric pipeline on this path.

## Monitoring Integration

N/A: desktop client, and the task adds no new signals.

- [ ] Prometheus metrics (N/A)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A)
- [ ] Log aggregation (N/A)

## Validation Results

- [x] Logs are correctly formatted (existing events unchanged; asserted ones are
      verified by the Step 4/5 green runs)
- [ ] Metrics are collected correctly (N/A: no metric change)
- [x] Logging works in error scenarios (cancellation logs asserted in the pre-start
      worker test and the explicit-budget teardown test)
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring (N/A)
- [x] `make verify-ai-tasks`: see the roadmap STEP 6 sub-items for the recorded result

## Follow-up Candidates for Step 7 (not implemented)

1. **Cancellation checkpoint is not identifiable from logs.**
   `collection_import_parse_worker_cancelled` carries only `path`. The pre-read,
   record (`done/total`) and post-read final-guard checkpoints all log the same line.
   A field such as `stage=pre_read|record|post_read` (plus `done`/`total` for the
   record stage) would let a field log show where a shutdown stopped the parse. That
   would be a production change, so it is outside PYPOST-1265.
2. **Cancellation shares the metric outcome `rejected` with file-picker dismissal
   (`path is None`).** `collection_import_file` uses `rejected` for both user/teardown
   cancellation (`_on_parse_cancelled`, `collection_import_actions.py:581`) and a
   dismissed file picker (`collection_import_actions.py:286-288`). Metrics cannot tell
   them apart. (The busy-skip path at `:282-284` only logs
   `collection_import_skipped reason=busy` and records no metric.) This is low priority and also a production change.
3. **Log coverage across the new tests is uneven (test-only, optional).** The
   teardown pre-start and default-budget teardown tests do not assert the presenter
   `collection_import_parse_cancelled` / `collection_import_worker_interrupted`
   events that the explicit-budget test asserts. Behaviour is fully covered, so this
   is not a gap in the acceptance criteria.

## Notes

The worker cancellation event is INFO and the presenter `collection_import_worker_interrupting`
event is WARNING. That matches the existing teardown contract (PYPOST-1229/1264) and is
not changed here.
