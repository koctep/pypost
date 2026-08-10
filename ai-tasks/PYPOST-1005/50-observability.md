# PYPOST-1005: Observability Implementation

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key components | `CollectionImportParseWorker`, `CollectionImportActions` |
| Critical paths | Pick file → start worker + busy cue → parse off GUI thread →
  clear cue → conflict/plan/apply (GUI) or invalid-file dialog |
| Existing coverage (PYPOST-987) | `collection_import_file_parsed`,
  `collection_import_file_invalid`, `collection_import_completed`,
  apply/reconcile/save-failed lines |
| Gap closed here | Async parse lifecycle (worker start/finish/fail), busy-cue
  show/clear, busy re-entry skip, finish-slot wait timeout |
| Intentionally not logged | Collection/request names, URLs, headers, bodies,
  full candidate lists, status-bar message text |

Critical execution path:

1. User picks a file; if `is_busy()`, INFO skip and return.
2. Orchestrator shows busy cue (button disabled + status) and starts
   `CollectionImportParseWorker`.
3. Worker runs `read_import_file` off-thread; emits completed or failed.
4. Orchestrator clears busy cue, then finishes import on the GUI thread
   (or shows invalid-file dialog).
5. Worker `finished` slot: `deleteLater` + bounded `wait` (WARNING if timeout).

## Logging Implementation

### Added Logs

Structured `key=value` events matching storage-async / encryption-migration
workers. PYPOST-987 terminal import lines are retained unchanged.

- **EMERG / ALERT / CRIT**: N/A — parse/import failures are recoverable,
  user-facing outcomes.
- **ERR**:
  - `collection_import_parse_worker_failed path=%s error=%s` in
    `pypost/core/qt/collection_import_parse_worker.py` — unexpected exception
    during parse (`exc_info=True`).
  - `collection_import_parse_unexpected error=%s` in
    `pypost/ui/presenters/collection_import_actions.py` — GUI-thread handling
    of that unexpected failure (invalid-file dialog path).
  - Existing apply ERR (PYPOST-987): `collection_import_save_failed` — unchanged.
- **WARNING**:
  - `collection_import_parse_worker_failed path=%s reason=%s` — worker saw
    `CollectionImportFileError` (structural/unreadable file).
  - `collection_import_file_invalid reason=%s` / `reason=no_valid_collections` —
    orchestrator terminal “nothing changed” outcomes (PYPOST-987 retained).
  - `collection_import_worker_finish_wait_timeout wait_ms=%d` — short join after
    `QThread.finished` did not complete (PYPOST-829 hygiene pattern).
- **NOTICE**: N/A (Python stdlib has no NOTICE level in use here).
- **INFO**:
  - `collection_import_skipped reason=busy` — second Import click ignored while
    parse is in flight (mirrors `load_collections_skipped reason=busy`).
  - `collection_import_parse_started path=%s` — orchestrator dispatched the
    parse worker (mirrors `collection_storage_async_load_dispatched`).
  - `collection_import_completed …` — flow-level completion with counts
    (PYPOST-987 retained).
  - Existing parse/apply INFO (PYPOST-987): `collection_import_file_parsed`,
    `collection_import_applied` — unchanged; still emitted from pure core when
    the worker calls `load_collection_import_candidates`.
- **DEBUG**:
  - `collection_import_parse_worker_started path=%s` — worker `run()` entered.
  - `collection_import_parse_worker_completed path=%s count=%d error_count=%d` —
    worker finished successfully (candidate count + per-record parse errors).
  - `collection_import_busy_cue_shown` — preparing cue activated (Import button
    disabled; status message shown when a status hook is injected).
  - `collection_import_busy_cue_cleared` — preparing cue cleared on parse
    success or failure (before conflict prompts / result dialog).

### Log Structure

Log format used:

- Structured logs: yes — `printf`-style `%s`/`%d` producing `key=value` tokens
- Includes context: yes — path at parse start/finish/fail; integer counts;
  short structural `reason` / `error` strings; `wait_ms` on finish timeout
- Log levels used: DEBUG, INFO, WARNING, ERROR

**Deliberately never logged:** request URLs, headers, bodies, scripts, MCP
schemas, collection/request names, full `parse_errors` lists, or the status-bar
string itself. Paths are logged for triage (user-chosen import file); names and
payloads stay out of the log.

## Metrics Implementation (if applicable)

### Performance Metrics

Not applicable. Import parse is a one-shot, user-initiated desktop action.
Latency is visible via the busy cue; no Prometheus scrape for GUI import parse
duration exists in this packaging, and sibling collection/env async tickets do
not add per-op histograms for equivalent paths.

### Business Metrics

Not applicable. Frequency and outcome rates are derivable from
`collection_import_parse_started` / `collection_import_completed` /
`collection_import_file_invalid` in log aggregation. No dedicated counter was
added (consistent with PYPOST-987).

### System Health Metrics

Not applicable. Worker finish wait timeout is a WARNING log only (same as
PYPOST-829 gateways); not exported as a metric.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable (desktop; see above)
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation (ELK, Loki, etc.) — structured `key=value` lines are
      consumable by the same pipeline as other PyPost operations

## Validation Results

Validation results:

- [x] Logs are correctly formatted — event names follow
      `collection_import_*` / `*_worker_*` conventions; verified by inspection of
      `collection_import_parse_worker.py` and `collection_import_actions.py`
- [x] Logging works in error scenarios — worker WARNING/ERR paths for
      `CollectionImportFileError` and unexpected exceptions; orchestrator
      WARNING invalid-file and ERR unexpected; finish wait WARNING
- [x] Large data structures are not logged — only path, counts, short reasons
- [x] Happy-path async lifecycle asserted via `caplog` in
      `tests/test_collections_import_ui.py::test_logs_completed_event_with_counts`
      (`collection_import_parse_started`, `collection_import_busy_cue_shown`,
      `collection_import_busy_cue_cleared`, `collection_import_completed`)
- [ ] Metrics available for monitoring — N/A, no metrics added

## Notes

- Worker DEBUG start/complete + orchestrator INFO dispatch matches
  `CollectionStorageWorker` / `CollectionsAsyncLoader` (internals DEBUG,
  dispatch INFO). Encryption migration uses INFO on the worker because that
  path is rare/bulk; import parse can be frequent, so worker stay DEBUG.
- Busy-cue events are DEBUG so default INFO logs stay focused on skip /
  dispatch / completion / invalid outcomes, while field triage can still
  confirm cue show/clear ordering when DEBUG is enabled.
- Dual logging of file-level failures (worker WARNING + orchestrator
  `collection_import_file_invalid`) is intentional: worker confirms off-thread
  failure; orchestrator emits the terminal “nothing changed” event name used
  since PYPOST-987.
