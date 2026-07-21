# PYPOST-877: Observability Implementation

## Scope

**TEST-HARNESS ONLY.** This task wires the environment-presenter async-load
encryption refresh check (and its hang-exit proof) onto the shared
`tests.helpers.process_until.process_until` helper already shipped by
PYPOST-823/827. **No production product code was changed** (`EnvPresenter`,
encryption, gateway/worker runtime unchanged by intent). Observability for
production logging, metrics, and monitoring integration is **N/A**.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key production components | Unchanged (`EnvPresenter`, encryption, environment storage) |
| Critical path under test | Nested wait for `environments_loaded` in env-presenter async-load check |
| Production logging gap | None; no production paths modified |
| Production metrics gap | None; desktop app has no Prometheus-style suite for this path |
| Test harness diagnostics | Shared `process_until` `AssertionError` + call-site hang-exit proof |

## Logging Implementation

### Added Logs

No new production logging. No new test harness logging either — failure signal
is a pytest `AssertionError` from `process_until`, not syslog-style log lines.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Log Structure

- Structured logs: N/A (no new logs)
- Includes context: N/A
- Log levels: none added

### Rationale (no production logging)

1. Scope is a consumer rewire of an existing shared test helper; product
   environment-presenter / encryption runtime behavior is intentionally
   unchanged.
2. There is no new production failure mode or branch to instrument.
3. Production INFO/DEBUG around env load for a harness-only hang fix would add
   noise without improving production incident response for this ticket.
4. Existing presenter logging covered by other tests in
   `tests/test_env_presenter.py` is unrelated to this wait port and was not
   extended.

## Metrics Implementation (if applicable)

### Performance Metrics

None added.

### Business Metrics

None added.

### System Health Metrics

None added.

### Rationale (no production metrics)

The check still verifies the same async outcomes (load completion + environment
list refresh). CI/local observability for hangs is the **time-bounded test
outcome** (fail within `timeout_ms`), not application metrics.

## Test-side diagnostics (non-production)

When the wall-clock deadline elapses without the predicate becoming true,
`tests/helpers/process_until.py` raises `AssertionError` with a neutral timeout
message (e.g. condition not met within `{timeout_ms}ms`). That assertion is the
observability surface for this task: maintainers see a clear pytest failure
instead of an indefinite nested-loop hang.

Consumers wired in this task:

- `test_async_load_refreshes_combo_when_encryption_enabled` —
  `process_until(lambda: bool(loaded), timeout_ms=5_000)`
- `test_async_load_wait_exits_near_deadline_when_never_complete` —
  hang-exit proof via `process_until(lambda: False, timeout_ms=300)` in a
  child process (clear `AssertionError` near deadline)

Canonical helper hang regressions (unchanged; remain in responsiveness module):

- `test_process_until_exits_on_wall_clock_deadline`
- `test_process_until_exits_via_posted_quit_without_poll_timer`

No `caplog` / metrics assertions for this port — failures surface as pytest
assertion errors, which is the appropriate signal for a quality-gate hang fix.
Richer timeout diagnostics (busy/pending / worker state in failure text) remain
out of scope ([PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828)).

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

**N/A** for this task (test harness only; no production monitoring hooks).

## Validation Results

Validation results:

- [x] No production logging or metrics required (harness-only scope)
- [x] Rationale documented above
- [x] Failure observability is via pytest `AssertionError` from `process_until`
- [x] Assertion message / test failure path is the observability surface (no
  large payloads)
- [x] Call-site hang-exit proof validates deadline exit for this module’s wait
- [x] Shared helper hang-regression tests remain the canonical wall-clock +
  posted-quit proofs
- [ ] Metrics available for monitoring — N/A
- [ ] Logs correctly formatted — N/A (no new logs)

## Notes

Production observability remains N/A unless a future ticket changes product
environment-presenter or encryption load lifecycle. If that happens, revisit
compact INFO/ERR around load completion and failures (flags and error string
only — not full environment payloads). For this ticket, maintainers rely on
pytest failure messages and hang-exit coverage of the shared helper at the
env-presenter call site.

Observability ready for production: **N/A** (no production path change);
harness failure signal is ready for CI.
