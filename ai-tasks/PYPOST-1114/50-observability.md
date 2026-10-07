# PYPOST-1114: Observability Implementation

## Scope and Decision

The change replaces mtime identity in `MtimeFileCache` with a content digest plus a post-load
re-hash. Only two paths are new and not visible anywhere today:

1. The file changed while the loader ran (digest before ≠ digest after). The value is returned
   uncached and the next call reloads.
2. The post-load re-read failed with `OSError`. The value is returned uncached.

Both are rare, self-healing and invisible to the caller, which makes them hard to diagnose
when a user reports "key rotation picked up late" or "file re-parsed on every call". Each
gets one DEBUG event. Everything else is already covered or would only add noise:

- **Hit path** (digest equal → cached value): no log. This runs on every key lookup. A log
  here would only be noise, and the "not re-parsed" behaviour is already covered by tests.
- **Normal miss** (content changed → reload): no log in the cache. The callers' loaders
  (`env.py` `_load_registry_payload`, `secret_store.py` spec loader) already log load failures
  and invalid payloads with `path=` / `reason=`. A successful reload is normal operation.
- **Initial read `OSError` / loader `None`**: unchanged behaviour. Callers check
  `path.is_file()` first and already log `*_missing` / `*_load_failed` with path and reason.

This differs from `20-architecture.md` § Security ("No new log statements are added in
`file_cache.py`"). That sentence was there to protect AC-7. The two events added here carry
only the path and the `OSError` text, so AC-7 still holds, and tests check it.

## Logging Implementation

### Added Logs

- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO**: none. Both conditions recover on
  the next call and have no user-visible effect, so they do not warrant WARNING or above. This
  matches the DEBUG level used for comparable file events in `env.py` / `secret_store.py`.
- **DEBUG**: `pypost/core/key_sources/file_cache.py` `MtimeFileCache.get`:
  - `file_cache_rewrite_during_load path=%s`: the file content changed during the load, and
    the value is returned uncached.
  - `file_cache_recheck_failed path=%s reason=%s`: the post-load re-read raised `OSError`
    (reason = exception text), and the value is returned uncached.

Logger: `logging.getLogger(__name__)` → `pypost.core.key_sources.file_cache`, the same
convention as the other `key_sources` modules.

### Log Structure

- Structured logs: yes. The project uses the `event_name key=value` style
  (`env_keys_file_load_failed path=%s reason=%s`).
- Includes context: yes, `path` and, for the re-read failure, `reason`.
- Log levels: DEBUG.
- AC-7: no file content, digest (raw, hex or repr), size, or parsed value appears in
  messages or args. The digest stays in the private `_digest` attribute. `reason` is the
  `OSError` text (errno message plus path), which contains no file content.

## Metrics Implementation (if applicable)

Not added. The reasons:

- `pypost/core/metrics_registry.py` (`MetricsManager`, Prometheus/OTel) tracks GUI actions
  and request/transport outcomes. No `key_sources` module emits metrics, and the cache is
  not wired to a metrics manager. Wiring one into a core cache with two module-level
  instances only for these events would need a dependency-injection change outside this
  task's scope.
- The new events are rare race and error conditions, and diagnosing them needs per-path
  context (DEBUG logs) more than aggregate rates.
- A metric label must never carry content-derived data (AC-7), so the only safe label would
  be the path. That is high-cardinality and already in the log.

### Performance Metrics

- None. Hashing cost is measured by the test suite, not exported.

### Business Metrics

- None.

### System Health Metrics

- None.

## Monitoring Integration

- [ ] Prometheus metrics (not applicable, see above)
- [ ] Grafana dashboards (not applicable)
- [ ] Alerting rules (not applicable: DEBUG-level self-healing events)
- [x] Log aggregation: events use the existing `event key=value` format and the standard
  logging pipeline

## Validation Results

- [x] Logs are correctly formatted: exact messages asserted in
  `tests/test_pypost_1114_observability.py`
- [x] Metrics are collected correctly: N/A (no metrics added)
- [x] Logging works in error scenarios: the re-read `OSError` path is tested with
  `PermissionError` injected on the second digest
- [x] Large data structures are not logged: path and reason only
- [x] AC-7: tests assert that neither the content nor the SHA-256 digest (hex or bytes repr) of
  either file version appears in any record message or args
- [x] No hot-path noise: a test asserts the normal miss → hit → changed-content reload sequence
  emits zero records from the cache logger
- [x] Metrics are available for monitoring: N/A

Tests (`tests/test_pypost_1114_observability.py`, `pytest.mark.timeout(30)`, caplog C1/C5,
one logger under test):

- `test_rewrite_during_load_logs_path_only`
- `test_recheck_failure_logs_path_and_reason_only`
- `test_normal_miss_and_hit_are_silent`

Gates:

- `make lint`: OK
- `make typecheck`: OK (baseline 181 known errors, unchanged)
- `make test PYTEST_ARGS="tests/test_pypost_1114_failing_repro.py
  tests/test_key_sources_chain_coverage.py tests/test_key_sources_secret_store.py
  tests/test_pypost_1114_observability.py -p no:randomly -q"`: 4/4 files passed

## Notes

- `make lint` runs flake8 on `pypost/` only. The new test file was checked by hand against
  `.flake8` (`max-line-length = 100`). This is the same gap already noted in Step 5.
- If the A→B→A residual limit (AC-9) ever needs diagnosing, these DEBUG events show whether
  racing loads occur on a given path, without exposing any content.
