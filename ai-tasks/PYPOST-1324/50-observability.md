# PYPOST-1324: Observability Implementation

## Logging Implementation

### Scope and Gap Analysis

Cooperative library cancel spans
`pypost/core/qt/library_operation_worker.py` (`cancel`, `run`) and
`pypost/ui/presenters/collection_import_actions.py` (teardown P0/P3,
`_on_library_operation_cancelled`). File-parse and shared-deadline fields from
PYPOST-1264 remain. This step closes gaps introduced by interrupt-then-bounded
library join.

Logs that existed after Step 4, and what they left unclear:

| Level | Event (fields) | Diagnostic value / gap |
| --- | --- | --- |
| WARNING | `collection_library_import_worker_cancelling` (no phase) | P0 and P3 used the same line; operators could not tell early stop from post-disconnect stop |
| INFO | `collection_library_import_worker_cancelled` (no fields) | Honored join had no `wait_ms` / `elapsed_ms`, unlike the timeout twin |
| WARNING | `collection_library_import_worker_timeout wait_ms= elapsed_ms=` | Still correct; after PYPOST-1324 `wait_ms` is `bounded(final_join_ms)`, not full remaining |
| INFO | `collection_library_import_operation_cancelled from_state=` | Signal path that clears `PREPARING` for P1 |
| DEBUG | `library_operation_worker_cancelled` | Shared-runner CTS cancel (worker-local) |

### Added Logs

Fields and phase tags only; event name stems are unchanged where reuse was required.

- **WARNING**: `collection_import_actions.py` teardown P0 —
  `collection_library_import_worker_cancelling phase=p0`. Early cooperative stop
  before wait-idle.
- **WARNING**: `collection_import_actions.py` teardown P3 —
  `collection_library_import_worker_cancelling phase=p3`. Post-disconnect stop
  immediately before the bounded final join.
- **INFO**: `collection_import_actions.py` teardown P3 —
  `collection_library_import_worker_cancelled wait_ms=%d elapsed_ms=%d`. Mirrors
  the timeout line: `wait_ms` is the join bound granted
  (`deadline.bounded(final_join_ms)`); `elapsed_ms` is from teardown start.
- **WARNING** (unchanged fields, clarified meaning): P3
  `collection_library_import_worker_timeout wait_ms=%d elapsed_ms=%d` — same
  scalars; `wait_ms` is no longer “remaining budget with no prior stop”.
- **INFO** (verified, not renamed):
  `collection_library_import_operation_cancelled from_state=%s`.
- **DEBUG** (verified, not renamed): `library_operation_worker_cancelled`.
- **EMERG / ALERT / CRIT / ERR / NOTICE**: none added. Unclean library join
  remains recoverable WARNING; cooperative cancel is INFO.

Considered and not added:

- Entry names, paths, or library payloads on cancel lines (NFR: no content/secrets).
- A separate event name for P3 vs P0: `phase=` keeps greppable stem stable.
- `final_join_ms` as a third field: it equals `wait_ms` whenever budget remains;
  when budget is exhausted, `wait_ms=0` already signals that.

### Log Structure

- Structured logs: yes (`event key=value` scalars, `%`-style lazy formatting)
- Includes context: yes (teardown phase, join bound, elapsed since deadline start,
  import state on signal cancel)
- Log levels: DEBUG, INFO, WARNING
- No library entry content, paths, or large structures on these events

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: no new series. Teardown duration stays on
  `collection_import_teardown_completed elapsed_ms=` (PYPOST-1264). Honored
  library join duration is visible as `wait_ms` / `elapsed_ms` on the cancelled
  or timeout library lines.
- **Throughput**: N/A
- **Error rate**: unclean library joins remain WARNING + `clean=False` on
  completed teardown.

### Business Metrics

- **`gui_library_operations_total`**: added allowlisted outcome `cancelled` in
  `pypost/core/metrics_registry.py` (`_LIBRARY_OPERATION_OUTCOMES`).
  `_on_library_operation_cancelled` now tracks
  `operation=collection_import_library, outcome=cancelled` instead of
  `rejected`, so cooperative teardown/stop is distinct from dialog
  selection/mode rejection (`rejected` unchanged).
- OTel tracker reuses the same allowlist via import; no separate OTel change.

### System Health Metrics

- **Resource usage**: N/A
- **Component status**: teardown cleanliness and library cancel/timeout lines as
  above; presenter lifecycle metrics unchanged (PYPOST-1321).

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`gui_library_operations_total` outcome label includes
  `cancelled`)
- [ ] Grafana dashboards (no new dashboard)
- [ ] Alerting rules (no new rules)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A for desktop; `key=value` greppable)

## Validation Results

Validation results:
- [x] Logs are correctly formatted — extended
  `tests/test_collection_import_teardown_policy.py`:
  - `test_teardown_timeout_logs_report_phase_waits_and_elapsed` asserts
    `phase=p0` / `phase=p3` cancelling lines plus timeout `wait_ms` /
    `elapsed_ms`
  - `test_library_join_success_logs_bounded_wait` asserts
    `collection_library_import_worker_cancelled wait_ms=30 elapsed_ms=30` and
    `clean=True`
  - `test_library_operation_cancelled_tracks_cancelled_outcome` asserts INFO
    `from_state=preparing`, MagicMock track call with `cancelled`, and
    Prometheus counter scrape for `outcome="cancelled"`
- [x] Metrics are collected correctly — registry allowlist accepts `cancelled`
  (unknown labels would normalize to `unknown`)
- [x] Logging works in error scenarios — unclean timeout path still covered
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring — outcome label on existing counter

Commands (this step):

- `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_teardown_policy.py
  tests/test_library_operation_interrupt_repro.py'` → 2/2 passed
- `make lint` → OK (flake8 `pypost/`; Markdown lint 17 files; relative links 19)
- `make typecheck` → mypy baseline OK (175 known errors; no new errors)
- `make verify-ai-tasks` → artifacts baseline OK

## Notes

- Operator reading guide: `phase=p0` without a later `phase=p3` join usually means
  the worker stopped during wait-idle (signal →
  `collection_library_import_operation_cancelled`) and P3 found it already idle.
  `phase=p3` plus `..._cancelled wait_ms=N` means the final join honored cancel
  within the short bound. `..._timeout wait_ms=N` with `N>0` means the op ignored
  cancel for that grace; `wait_ms=0` means an earlier phase used the budget.
- Dialog cancels at selection/mode still log
  `collection_library_import_cancelled stage=...` and metric `rejected`.
- Step 8 should update `doc/dev/collection_import.md` for `phase=`, cancelled
  success fields, and the metrics `cancelled` outcome (docs still describe
  join-only P3 / older field sets in places).
