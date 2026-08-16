# PYPOST-1076: Observability Implementation

## Observability Requirements Analysis

PYPOST-1076 is a verification-only closure of a native process-crash report. Commit
`17c20fb9180b05efd16ac04f17dd630efcd16cc1` already separates domain-result delivery from native
`QThread.finished()` cleanup and supplies the lifecycle logging needed to diagnose the affected
path. The current tree has no scoped production or test diff against that commit, so Step 6 did
not add or alter production logging.

The critical observable sequence for a confirmed re-encryption is:

1. The settings section records UI dispatch.
2. The worker records entry into the selected operation.
3. The worker records either a returned report or an exception.
4. On success, the settings section records result handling while ownership is still retained.
5. Native `QThread.finished()` triggers deletion, a bounded 100 millisecond wait, ownership
   release, and control restoration. Only an expired wait produces a warning.

This sequence distinguishes a domain result from native thread termination without logging
settings, encryption values, environment collections, or complete report payloads.

## Logging Implementation

### Exact Structured Events

- **INFO**, logger `pypost.ui.dialogs.settings_dialog`:
  `settings_encryption_%s_started` — the UI accepted and dispatched `re_encrypt` or
  `encrypt_plaintext`.
- **INFO**, logger `pypost.core.qt.encryption_migration_worker`:
  `encryption_migration_worker_started operation=%s` — worker execution entered for the named
  operation.
- **INFO**, logger `pypost.core.qt.encryption_migration_worker`:
  `encryption_migration_worker_completed operation=%s success=%s` — the service returned a
  report immediately before `succeeded(report)` is emitted.
- **INFO**, logger `pypost.ui.dialogs.settings_dialog`:
  `settings_encryption_%s_completed success=%s backup=%s error_count=%d` — the UI handled the
  domain result and requested presentation before native lifecycle cleanup.
- **WARNING**, logger `pypost.ui.dialogs.settings_dialog`:
  `settings_encryption_migration_worker_finish_wait_timeout wait_ms=%d operation=%s` — Qt emitted
  native completion, but bounded `wait(100)` returned false. Cleanup remains bounded and controls
  are restored.
- **ERROR**, logger `pypost.core.qt.encryption_migration_worker`:
  `encryption_migration_worker_failed operation=%s error=%s` — the service raised; the event
  includes traceback context through `exc_info=True`.
- **ERROR**, logger `pypost.ui.dialogs.settings_dialog`:
  `settings_encryption_migration_worker_failed error=%s` — the UI handled and presented the
  worker failure.
- **INFO**, logger `pypost.ui.dialogs.settings_dialog`:
  `settings_encryption_%s_cancelled` — the user declined a bulk operation; no worker was started.
- **INFO**, logger `pypost.ui.dialogs.settings_dialog`:
  `settings_encryption_verify_started` — synchronous encryption verification began.
- **INFO**, logger `pypost.ui.dialogs.settings_dialog`:
  `settings_encryption_verify_completed success=%s error_count=%d` — synchronous verification
  returned its result.

The cleanup-warning test asserts this exact rendered event:

```text
settings_encryption_migration_worker_finish_wait_timeout wait_ms=100 operation=re_encrypt
```

`EMERG`, `ALERT`, `CRIT`, `NOTICE`, and `DEBUG` are N/A. The lifecycle has no condition needing
those severities, and Python standard logging has no `NOTICE` level. A process-level bus error
cannot reliably emit a Python log after the signal; native crash artifacts are therefore part of
the escalation diagnostics below rather than a speculative Python logging change.

### Log Structure and Privacy

- Structured logs: yes; each message has a stable event prefix and bounded `key=value` fields.
- Context: operation, success, error count, optional backup path, cleanup bound, and concise error
  text.
- Levels used: INFO, WARNING, and ERROR.
- Large or sensitive values are excluded: no settings object, environment collection, encryption
  value, complete migration report, or error collection is logged.
- Worker events locate off-thread execution; settings events locate UI dispatch and presentation.
  These are separate lifecycle boundaries rather than duplicate reports of one event.

## Metrics Implementation

### Performance Metrics

N/A. Encryption migration is an infrequent, user-initiated desktop maintenance operation, and
PYPOST-1076 changes no runtime behavior. The 100 millisecond cleanup bound is a correctness guard,
not a latency objective. Introducing a metrics dependency solely for verification would expand
the production interface without improving diagnosis of a native crash.

### Business Metrics

N/A. The ticket adds no business operation or outcome. Existing start and terminal events provide
bounded per-execution evidence without collecting product analytics.

### System Health Metrics

N/A. The actionable runtime condition is already represented by the cleanup-timeout WARNING. A
counter would duplicate this rare desktop event, while a process-level crash must be diagnosed
from the process status and macOS crash report.

## Monitoring Integration

- [ ] Prometheus metrics — N/A; no task-specific metric is warranted.
- [ ] Grafana dashboards — N/A; this desktop path has no service-level objective or metric.
- [ ] Alerting rules — N/A; deployment and alerting configuration are outside this task.
- [ ] Log aggregation changes — N/A; existing stable event prefixes work with configured logging
  handlers and require no new integration.

## Validation Evidence

Step 4 independently validated the unchanged commit on the affected platform. Step 6 relies on
that stronger platform evidence and did not substitute a run under a different interpreter.

- Platform: macOS 15.7.7 arm64, CPython 3.13.13, with a 64-bit arm64 Mach-O Python executable.
- Environment installation exited 0 in 20.67 seconds.
- Focused validation passed all 14 worker and Settings UI tests in 0.50 seconds (5.68 seconds wall
  time). It covers exactly-once confirmed re-encryption, result presentation, retained ownership,
  native completion cleanup, the exact warning above, reference release, and restored controls.
- Full run 1 reached 100% with 2,197 passed, 5 failed, 22 deselected, and 1 warning in 528.34
  seconds (531.93 seconds wall time; baseline-relative exit 2).
- Full run 2 reached 100% with 2,197 passed, 5 failed, 22 deselected, and 1 warning in 528.27
  seconds (529.90 seconds wall time; baseline-relative exit 2).
- Every migration test passed in both full runs, and execution continued through the remaining
  suite. Neither run produced a bus error, fatal interpreter error, hang, or process-level
  termination.
- The five failures in each run exactly match the separately documented PYPOST-1071 baseline and
  do not represent missing observability or a PYPOST-1076 regression.
- `test_run_logs_error_on_failure` captures the worker ERROR logger and asserts the stable
  `encryption_migration_worker_failed` event prefix.
- `test_migration_worker_logs_bounded_cleanup_timeout` uses `caplog` at WARNING level for the
  settings logger and asserts the exact rendered warning plus bounded cleanup behavior.
- Both test modules declare explicit pytest timeouts; the live Qt helper also has an
  assertion-producing 5,000 millisecond internal bound with worker-running and operation context.

## Native-Failure Escalation Diagnostics

If a bus error, fatal interpreter error, hang, or other process-level termination recurs, stop the
verification-only closure and preserve one evidence packet before attempting a code change:

1. Record commit SHA and scoped worktree diff, exact test command, start/end timestamps, wall
   duration, exit status or terminating signal, and the last collected pytest node.
2. Record `sw_vers`, `uname -m`, Python `-VV`, `sys.executable`, `platform.machine()`, and the
   executable's Mach-O architecture. Also retain the active Qt/PySide version and
   `QT_QPA_PLATFORM` value.
3. Preserve stdout and stderr, including the last lifecycle event prefix. The sequence shows
   whether failure occurred before worker entry, before domain completion, between domain result
   presentation and native completion, or after cleanup.
4. Preserve the matching macOS diagnostic report from `~/Library/Logs/DiagnosticReports`,
   including exception type, termination reason, crashed thread, and native backtrace. Redact
   unrelated paths or user data before sharing; do not add settings or encryption payloads.
5. For a hang, preserve the bounded-wait assertion detail (`worker_running` and
   `worker_operation`) and a process sample or debugger thread backtrace instead of allowing an
   unbounded wait.
6. Compare focused and full-suite behavior on the same interpreter and unchanged tree. Open a
   newly scoped defect from the captured evidence if it contradicts the two conclusive runs above;
   do not increase waits or force thread termination merely to suppress a warning.

## Gate Status

Observability is ready for gate review. Existing production events and automated logging
contracts cover the critical path, affected-platform evidence is conclusive, and no new metric or
production change is justified. Step 6 remains `[/]`; the gate owner decides whether to mark it
`[x]`.
