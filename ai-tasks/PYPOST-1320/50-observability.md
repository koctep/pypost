# PYPOST-1320: Observability Implementation

## Decision

**No production logging or metrics change.** PYPOST-1320 replaces per-wait
`threading.Timer.start` with a module-scoped `_DeadlineScheduler` inside
`tests/helpers/process_until.py` and adds a focused hang-repro test. Product
modules under `pypost/` are unchanged (`git` / architecture: harness-only by
default). Completion Criteria are met by documenting that production
observability is out of scope and that existing test-side diagnostics already
cover the failure classes this ticket cares about.

Adding syslog-style logs inside the deadline scheduler would be counterproductive:
the hang class is a logging-lock × limbo-lock race triggered by QThread
`exc_info=True` logging. Extra helper logging on the arm/fire path would add
contention and noise without a production consumer.

## Observability Requirements Analysis

| Path | Production relevance | Monitoring need |
| --- | --- | --- |
| `_DeadlineScheduler` / `_arm_posted_quit` | Test helper only; daemon thread name `process-until-deadline` | None — silent enqueue / cancel / fire |
| `process_until` timeout assert | Test harness | Existing `AssertionError` + optional `timeout_detail` (PYPOST-828) |
| Product `CollectionImportParseWorker` `logger.error(..., exc_info=True)` | Unchanged trigger, not the fix target | Existing product ERROR path unchanged |
| Parallel-runner / pytest timeouts | CI quality gate | Already kill / fail workers when main stays blocked (pre-fix symptom) |

Critical execution path under this ticket is **arming a posted-quit deadline without
`Thread.start` while a QThread may hold logging/limbo locks** — a pytest-worker
concern, not a shipped-app operation.

## Logging Implementation

### Added Logs

No logging added to `tests/helpers/process_until.py`, the watchdog repro, or any
`pypost/` module.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Why not add test-helper logs

1. Scope is harness-only; requirements forbid intentional product rewrites for this hang.
2. The scheduler’s success signal is a finishing wait (predicate true or timely
   `AssertionError`), not a log line.
3. Logging from the daemon or arm path risks the same lock family that caused the hang.
4. Maintainers triage from pytest failure text and Make / parallel-runner outcomes —
   the same channel as PYPOST-823 / PYPOST-827 / PYPOST-828.

### Log Structure

- Structured logs: N/A (no new logging)
- Includes context: N/A
- Log levels: N/A

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A — hang/timeout remain pytest / runner failures, not Prometheus

### Business Metrics

- N/A — no product import/UX behavior change

### System Health Metrics

- **Resource usage**: N/A
- **Component status**: N/A

## Test-side diagnostics (primary observability channel)

Retained unchanged from PYPOST-828; this step only inventories them against the
new scheduler.

### Timeout `AssertionError` (unchanged)

When the wall-clock deadline elapses with the predicate still false:

```text
condition not met within {timeout_ms}ms
(wall-clock deadline; predicate still false)[; <timeout_detail>]
```

| Helper | Role |
| --- | --- |
| `timeout_detail` kwarg | Lazy callable evaluated **only on timeout** |
| `format_storage_async_timeout_detail` | Formats `busy=` / `pending=` / optional worker fields |
| `gateway_timeout_detail(gateway)` | Shared lazy snapshot for gateway waits |

Detail failures never mask the timeout (`timeout_detail failed: <Type>: <exc>`).

### Failure modes (CI / maintainer reading guide)

| Failure mode | How it surfaces | What it means after this fix |
| --- | --- | --- |
| Predicate never true, wait finishes | `AssertionError` with timeout text (+ optional detail) | Normal deadline path; poll timer and/or posted quit ended `exec()` |
| Hang-regression (`use_poll_timer=False`) | Same `AssertionError` near `timeout_ms` via posted quit only | Scheduler-driven `QTimer.singleShot(0, loop, loop.quit)` still proves non-poll wake |
| Historical Timer.start × QThread `exc_info` hang | Pre-fix: worker stuck until parallel-runner ~120 s kill; pytest-timeout never fired | Mitigated: arm no longer calls `Thread.start` on the hot path; repro asserts exit within ~2×`timeout_ms` |
| Watchdog repro bound exceeded | `AssertionError` in `test_process_until_exits_near_deadline_under_qthread_exc_info` mentioning historical `Timer.start` / limbo diagnosis | Scheduler regression or new limbo contention — investigate helper, not product logs |
| Scheduler bootstrap on first arm | Still one `Thread.start` at first helper use (daemon `process-until-deadline`) | Outside contended wait window after warmup; later arms only enqueue |

### Coverage of the diagnostic channel

- `tests/test_process_until_diagnostics.py` — timeout text, detail helpers, detail failure safety
- `tests/test_env_storage_responsiveness.py` — wall-clock + posted-quit-without-poll hang-regression
- `tests/test_process_until_watchdog_repro.py` — no hang under QThread limbo / `exc_info` logging

No `caplog` / metrics assertions — pytest `AssertionError` text and bounded exit are
the appropriate signals.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics (N/A — test harness only)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A — CI fails the Make gate on timeout / non-zero worker exit)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A — no new log events)

## Validation Results

Validation results:

- [x] No production logs or metrics required for this change set
- [x] Helper remains without logger calls (source inspection of `process_until.py`)
- [x] Existing `timeout_detail` / `gateway_timeout_detail` contract retained
- [x] Hang / timeout failure modes documented above for CI triage
- [x] Large data structures are not logged (no logging added; detail helpers stay scalar)
- [ ] Metrics are collected correctly (N/A)
- [ ] Metrics are available for monitoring (N/A)
- [ ] Logs are correctly formatted (N/A — no new logs)

## Notes

- This step changes task documentation only (`50-observability.md` + roadmap Step 6
  notes). No `pypost/`, `tests/`, or Makefile edits in Step 6.
- Step 8 should update `doc/dev/gui_testing.md` / `doc/dev/testing.md` wording that still
  says per-wait daemon `threading.Timer` so docs match the shared scheduler (architecture
  already calls this out).
- Follow-ups (if any) for optional scheduler DEBUG under an env flag belong in Step 7
  tech debt — not default production or harness logging for this ticket.
