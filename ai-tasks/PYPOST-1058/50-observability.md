# PYPOST-1058: Observability Implementation

## Logging Implementation

### Context and Observability Analysis

In PYPOST-1004, save failure recovery was implemented to reconcile in-memory collection state with durable disk storage (`manager.reload_collections()`). In PYPOST-1058, the collection import lifecycle was extended to ensure that the outcome statistics reported to both the user and the observability pipeline accurately reflect durable storage after partial save failures.

When `apply_imported_collections` encounters an `OSError` writing one or more collections, it returns a `CollectionImportApplyResult` containing the failed collection IDs (`failed_ids`). `CollectionImportActions._finish_import` passes these failed IDs to `recount_collection_import_plan` before emitting the final summary and logging `collection_import_completed`.

This guarantees that:
1. Low-level write errors are captured per collection with error context.
2. In-memory state reconciliation is explicitly flagged as a warning event.
3. Apply-level operation summary records total planned, persisted, and failed write counts.
4. UI-level completion event records recounted, durable-aligned numbers for added, updated, renamed, and total request counts alongside error counts.

### Key Lifecycle Logs

- **ERROR**: `pypost/core/collection_import_apply.py::apply_imported_collections`
  - Event: `collection_import_save_failed collection_id=%s error=%s`
  - Emitted when `manager.storage.save_collection(col)` raises `OSError`.
  - Captures the specific failed collection ID and the underlying OS error message without interrupting writes for other collections.

- **WARNING**: `pypost/core/collection_import_apply.py::apply_imported_collections`
  - Event: `collection_import_reconciled failed_count=%d collection_count=%d`
  - Emitted after `manager.reload_collections()` executes when `failures` is non-empty.
  - Documents that memory was reconciled back to durable disk state, reporting the count of failed saves and the resulting in-memory collection count.

- **INFO**: `pypost/core/collection_import_apply.py::apply_imported_collections`
  - Event: `collection_import_applied collection_count=%d persisted_count=%d failed_count=%d`
  - Emitted at the end of `apply_imported_collections`.
  - Summarizes the apply operation: planned collections count, persisted subset count, and total write failures.

- **INFO**: `pypost/ui/presenters/collection_import_actions.py::CollectionImportActions._finish_import`
  - Event: `collection_import_completed added_count=%d updated_count=%d skipped_count=%d renamed_count=%d request_count=%d error_count=%d`
  - Emitted after applying imports, recounting against durable storage (if save errors occurred), and refreshing the UI tree.
  - **PYPOST-1058 Enhancement**: Logs durable-aligned recounted counts (`result.added`, `result.updated`, `result.skipped`, `result.renamed`, `result.request_count`, `result.parse_errors`), preventing phantom additions/updates from polluting metric aggregations.

### Additional Supporting Lifecycle Logs

- **INFO**: `pypost/ui/presenters/collection_import_actions.py`
  - `collection_import_parse_started path=%s` — logged when file parsing begins off-thread.
  - `collection_import_skipped reason=busy` — logged when import is triggered while a parse worker is active.
- **WARNING / ERROR**: `pypost/ui/presenters/collection_import_actions.py`
  - `collection_import_file_invalid reason=%s` (WARNING) — logged when file has no usable collections or syntax errors.
  - `collection_import_worker_finish_wait_timeout wait_ms=%d` (WARNING) — logged if worker thread wait exceeds bound.
  - `collection_import_parse_unexpected error=%s` (ERROR) — logged on unexpected non-file parse errors.
- **DEBUG**: `pypost/ui/presenters/collection_import_actions.py`
  - `collection_import_busy_cue_shown` / `collection_import_busy_cue_cleared` — logged when UI busy state changes.
- **DEBUG / INFO / WARNING / ERROR**: `pypost/core/qt/collection_import_parse_worker.py`
  - `collection_import_parse_worker_started path=%s` (DEBUG)
  - `collection_import_parse_worker_completed path=%s count=%d error_count=%d` (INFO)
  - `collection_import_parse_worker_failed path=%s reason=%s` (WARNING / ERROR)
- **INFO**: `pypost/core/collection_import.py`
  - `collection_import_file_parsed path=%s candidate_count=%d error_count=%d` (INFO)

### Log Structure

- **Structured logs**: Yes, standard `key=value` format via printf-style format strings.
- **Includes context**: Yes (collection IDs, counts, error reasons, file paths).
- **Log levels used**:
  - `ERROR`: Unhandled exceptions, file save failures (`OSError`), unexpected worker crashes.
  - `WARNING`: Reconciliation events after mid-write failure, invalid import files, thread wait timeouts.
  - `INFO`: Normal lifecycle boundaries (parse started, applied summary, completed outcome with counts).
  - `DEBUG`: Busy cue toggles, worker lifecycle start.
- **Sensitive data policy**: No collection payload data, request headers, request bodies, auth tokens, or scripts are output to logs; only IDs, counts, and error descriptions.

## Metrics Implementation (if applicable)

### Performance Metrics

Not applicable. Collection import is an on-demand, user-initiated operation. Recounting in `recount_collection_import_plan` is a fast in-memory pure calculation over small lists (`O(N)` where `N` is number of imported collections), adding negligible overhead (<1ms) only on the error recovery path.

### Business Metrics

Not applicable. Operational metrics such as import success/failure rates and recount frequencies can be extracted directly from structured logs (`collection_import_completed`, `collection_import_reconciled`, `collection_import_save_failed`).

### System Health Metrics

Not applicable. Underlying disk/filesystem health issues during collection persistence are captured via `collection_import_save_failed` error events.

## Monitoring Integration

- [ ] Prometheus metrics (N/A for desktop client import action)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A)
- [x] Log aggregation (ELK, Loki, syslog) — structured `key=value` log lines easily indexable by log collectors.

## Validation Results

- [x] Logs are correctly formatted: All log statements adhere to `event_name key1=val1 key2=val2` convention.
- [x] Metrics are collected correctly: N/A.
- [x] Logging works in error scenarios:
  - Validated via `pytest tests/test_collection_import_apply.py` (`caplog` checks for `collection_import_save_failed` and `collection_import_reconciled`).
  - Validated via `pytest tests/test_collections_import_ui.py` (`caplog` checks for `collection_import_completed`, `collection_import_file_invalid`, etc.).
- [x] Large data structures are not logged: Only counts and IDs are logged.
- [ ] Metrics are available for monitoring: N/A.

## Notes

### Diagnostic Sequence During Save Failure

When a disk write failure occurs during collection import persistence, operators will see the following chronological sequence of log events:

1. **ERROR**: `collection_import_save_failed collection_id=<id> error=<disk error>` (one per failed write)
2. **WARNING**: `collection_import_reconciled failed_count=<N> collection_count=<M>` (in-memory state reloaded to match disk)
3. **INFO**: `collection_import_applied collection_count=<total_planned> persisted_count=<persisted> failed_count=<N>`
4. **INFO**: `collection_import_completed added_count=<recounted_added> updated_count=<recounted_updated> skipped_count=<skipped> renamed_count=<recounted_renamed> request_count=<recounted_requests> error_count=<errors>` (accurately reflecting durable state)
