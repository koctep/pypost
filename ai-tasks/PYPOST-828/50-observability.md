# PYPOST-828: Observability Implementation

## Scope

**TEST-HARNESS ONLY.** This task enriches timeout `AssertionError` text in
`tests/helpers/process_until.py` (optional lazy `timeout_detail`, shared
formatters, call-site wiring). **No production product code was changed.**
Production logging, metrics, and monitoring integration are **N/A**.

The assertion message **is** the diagnostic channel for this ticket.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key production components | Unchanged (env/collection gateways and workers) |
| Critical path under test | Hang-resistant Qt waits for storage async load/save |
| Production logging gap | None; no production paths modified |
| Production metrics gap | None; desktop app has no Prometheus suite for this path |
| Test harness diagnostics | Richer `AssertionError` with duration, reason, optional snapshot |

Critical execution path (test only):

1. Test starts async work and waits via `process_until`.
2. On success: no diagnostic callable; no extra output.
3. On timeout: compose `AssertionError` with `timeout_ms`, neutral reason, and
   (when provided) lazy `timeout_detail()` snapshot (busy/pending and/or worker).

## Logging Implementation

### Added Logs

No new production logging. No new test-harness syslog-style logging either —
failure signal is a pytest `AssertionError` from `process_until`, not log lines.

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

1. Requirements and architecture confine the change to the test harness; product
   gateway/worker runtime behavior is intentionally unchanged.
2. There is no new production failure mode or branch to instrument.
3. Busy/pending and optional worker state are already exposed via public gateway
   APIs (`is_busy()`, `has_pending_work()`) and worker `isRunning()`; the harness
   reads them only at timeout for the failure message.
4. Adding INFO/DEBUG around production load/save for a harness-only triage fix
   would add noise without improving production incident response for this
   ticket.
5. Maintainers triage from CI pytest output; that is the intended audience and
   channel (same pattern as PYPOST-823 / PYPOST-827).

## Metrics Implementation (if applicable)

### Performance Metrics

None added.

### Business Metrics

None added.

### System Health Metrics

None added.

### Rationale (no production metrics)

Pass/fail and hang-defense deadlines are unchanged. CI/local observability for
timeouts is the **enriched pytest failure message**, not application metrics
(throughput, latency histograms, or Prometheus scrapes).

## Test-side diagnostics (primary observability channel)

### Assertion message as diagnostic surface

When the wall-clock deadline elapses without the predicate becoming true,
`tests/helpers/process_until.py` raises `AssertionError` with:

```text
condition not met within {timeout_ms}ms
(wall-clock deadline; predicate still false)[; <timeout_detail>]
```

Optional detail is evaluated **only on timeout** (lazy snapshot at deadline):

| Helper | Role |
| --- | --- |
| `timeout_detail` kwarg | Caller-supplied `Callable[[], str]` appended after `; ` |
| `format_storage_async_timeout_detail` | Formats `busy=`, `pending=`, optional |
| | `worker_running=` / `worker_operation=` (omit `None`) |
| `gateway_timeout_detail(gateway)` | Shared lazy snapshot for gateway waits |

Example (gateway wait):

```text
condition not met within 10000ms (wall-clock deadline; predicate still false);
busy=True pending=True worker_running=True
```

### Detail failure safety

If `timeout_detail()` raises, the timeout `AssertionError` still fires with a
compact note (`timeout_detail failed: <Type>: <exc>`). Detail errors never mask
the timeout or extend the deadline.

### What is not logged

- No full environment/collection payloads
- No large Qt object dumps
- No success-path diagnostic calls (callable not invoked on pass)

### Coverage of the diagnostic channel

Focused tests in `tests/test_process_until_diagnostics.py` plus hang-regression
coverage in the responsiveness module validate:

- Default message remains actionable without a callback
- Busy/pending (and optional worker) appear when `timeout_detail` reports them
- Detail callable exceptions do not mask the timeout
- Hang defense still exits within ~300 ms

No `caplog` / metrics assertions — pytest `AssertionError` text is the
appropriate signal for quality-gate timeout triage.

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
- [x] Observability surface is pytest `AssertionError` from `process_until`
- [x] Timeout text includes duration + neutral reason (+ optional detail)
- [x] Large data structures are not included in the failure message
- [x] Detail evaluation is post-wait only (does not change hang-defense timing)
- [ ] Logs correctly formatted — N/A (no new logs)
- [ ] Metrics available for monitoring — N/A

## Notes

- PYPOST-823 / PYPOST-827 established hang-resistant waits and deferred richer
  timeout text; this ticket closes that deferred diagnostic item only.
- Production observability remains N/A unless a future ticket changes product
  gateway/worker lifecycle. If that happens, revisit compact INFO/ERR around
  worker finish and load_failed (flags and error string only — not full
  payloads).
- Step 7 should note the richer timeout text in `doc/dev/gui_testing.md` if the
  old default message is still quoted there.
