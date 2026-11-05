# PYPOST-1321: Observability Implementation

## Logging Implementation

### Scope and Gap Analysis

PYPOST-1321 admits `CollectionsPresenter` as a main-window shutdown owner. Step 4 already
wired peer-shaped lifecycle logging in
`pypost/ui/presenters/collections_presenter_lifecycle.py` and kept the PYPOST-1264
diagnostic lines. This step verifies that surface, closes a metrics-label gap, and adds
regression coverage.

Critical path under observation:

1. `main_window_lifecycle.teardown` — fences non-last owners (including collections),
   allocates a fair share, aggregates `TeardownResult`s.
2. `collections_presenter_lifecycle.begin_teardown` / `teardown` — fences import admission,
   runs import teardown under the caller budget, closes the panel.
3. `collection_import_actions.teardown` — PYPOST-1264 phase logging (unchanged).

### Added / Corrected Observability

- **INFO** (already present from Step 4; verified here):
  `collections_presenter_lifecycle.teardown` —
  `lifecycle_teardown_started owner=collections_presenter teardown_id=%s timeout_ms=%d
  active_count=%d pending_count=%d` and matching `lifecycle_teardown_completed` with
  `outcome`, `elapsed_ms`, `deadline_ms`, counts. Correlation id is inherited from the
  main-window run when present (`main_window_lifecycle` stamps
  `_teardown_correlation_id` on each owner before the loop).
- **INFO** (kept for PYPOST-1264 callers):
  `collections_presenter_teardown_started timeout_ms=%d` and
  `collections_presenter_teardown_completed clean=%s`.
- **INFO** (unchanged peer path): `main_window` `lifecycle_teardown_started` now reports
  `owner_count=5` when collections is present (tabs, history_panel, history_manager,
  collections, env).
- **EMERG / ALERT / CRIT / ERR / NOTICE / DEBUG**: none added for this owner registration.
  Unclean import teardown remains WARNING on the actions path (PYPOST-1264).

### Log Structure

- Structured logs: yes (`event key=value` scalars, `%`-style lazy formatting)
- Includes context: yes (`teardown_id`, owner name, budget/deadline, active/pending counts,
  outcome, elapsed)
- Log levels used on this path: INFO (presenter/main-window lifecycle), plus existing
  WARNING/DEBUG on import actions
- No collection payloads, file contents, or large structures are logged

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: `lifecycle_teardown_duration_seconds` via
  `record_teardown_metrics` → `MetricsRegistry.track_lifecycle_teardown` /
  OTel equivalent, labeled `owner=collections_presenter`.
- **Throughput**: N/A (one teardown attempt per shutdown run; idempotent replay does not
  re-record).
- **Error rate**: `lifecycle_teardowns_total{owner="collections_presenter",outcome=...}`
  for `success` / `incomplete` / `failed`.

### Business Metrics

- None added. Existing import `track_*` / library operation metrics are unchanged.

### System Health Metrics

- **Component status**: `lifecycle_teardown_active_workers` and
  `lifecycle_teardown_pending_work` gauges for `owner=collections_presenter` (snapshot at
  teardown start counts).
- **Fix (this step)**: `_LIFECYCLE_OWNERS` in `pypost/core/metrics_registry.py` did not
  include `collections_presenter`, so Step 4's `record_teardown_metrics` calls would
  normalize the owner label to `unknown`. Added `collections_presenter` to the allowlist
  so Prometheus/OTel labels match the log `owner=` field and `_LIFECYCLE_OWNER_BY_CLASS`.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`MetricsRegistry` counters/gauges/histograms; desktop scrape when
  enabled)
- [ ] Grafana dashboards (no new dashboard in this task)
- [ ] Alerting rules (no new rules; incomplete shutdown remains visible via outcome labels)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A for desktop; `key=value` greppable)

## Validation Results

Validation results:
- [x] Logs are correctly formatted — new test
  `test_collections_teardown_emits_correlated_lifecycle_log_and_metrics` asserts one
  correlated `lifecycle_teardown_started` / `_completed` pair, legacy
  `collections_presenter_teardown_*` lines, and `deadline_ms=100`
- [x] Metrics are collected correctly — same test asserts
  `lifecycle_teardowns_total{...,owner="collections_presenter"}` and
  `lifecycle_teardown_active_workers{owner="collections_presenter"}`
- [x] Logging works in error scenarios — unclean paths remain covered by PYPOST-1264
  policy/repro tests (`collection_import_*_timeout`, `clean=False`); idle success path
  covered here
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring — owner allowlist fix unblocks labeled scrapes
- [x] Main-window aggregate harness includes collections — 
  `test_main_window_aggregate_logs_and_metrics_one_correlated_attempt` expects
  `owner_count=5` and `collections.begin_calls == 1`

Commands (run this step):

- `make test WORKERS=1 PYTEST_ARGS='tests/test_lifecycle_observability.py
  tests/test_main_window_collections_shutdown_repro.py
  tests/test_collection_import_teardown_policy.py'` → 3/3 passed
- `make lint` → OK (flake8 `pypost/`; Markdown lint 17 files; relative links 19)
- `make typecheck` → mypy baseline OK (175 known errors; no new errors)

## Notes

- Operator reading guide: join main-window and collections lines on `teardown_id=`. The
  collections `timeout_ms` / `deadline_ms` is the fair share granted by the main-window
  allocator, not the full application budget. Legacy `collections_presenter_teardown_*`
  lines lack `teardown_id`; prefer `lifecycle_teardown_*` for cross-owner correlation.
- Step 8 may note `collections_presenter` in lifecycle metrics owner docs if those lists
  are enumerated in `doc/dev/`.
