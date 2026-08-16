# PYPOST-1072: Observability Implementation

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key components | `EncryptionMigrationSection`, `EncryptionMigrationWorker` |
| Critical path | Dispatch, domain outcome, native thread completion, bounded cleanup |
| Existing coverage | Structured start, completion, cancellation, and failure events |
| Gap closed | Automated validation of the new bounded cleanup timeout warning |

The worker lifecycle fix changes ownership and cleanup timing, not migration business behavior.
The important production diagnostic is whether the bounded `wait(100)` fails after Qt reports
thread completion. A warning is sufficient because cleanup remains bounded, the worker reference
is released, and the settings controls are restored.

## Logging Implementation

### Added Logs

The implementation already added this production event in
`pypost/ui/widgets/settings/encryption_migration_section.py`:

- **WARNING**:
  `settings_encryption_migration_worker_finish_wait_timeout wait_ms=%d operation=%s` — the
  short join did not complete within 100 milliseconds. Context identifies the bound and the
  migration operation without logging settings, environment data, or a report payload.

Step 6 added an automated `caplog` assertion for the exact rendered event and verified that the
worker reference is still cleared and the migration control is restored after the warning.

No additional production logs were necessary. The existing events remain:

- **ERROR**:
  - `encryption_migration_worker_failed operation=%s error=%s` — service exception in the
    worker, with traceback via `exc_info=True`; logger
    `pypost.core.qt.encryption_migration_worker`.
  - `settings_encryption_migration_worker_failed error=%s` — UI outcome handler reports the
    user-visible migration failure; logger `pypost.ui.dialogs.settings_dialog`.
- **INFO**:
  - `encryption_migration_worker_started operation=%s` — worker execution entered.
  - `encryption_migration_worker_completed operation=%s success=%s` — service returned a
    report and the domain result is about to be emitted.
  - `settings_encryption_verify_started` — synchronous verification began.
  - `settings_encryption_verify_completed success=%s error_count=%d` — verification result.
  - `settings_encryption_%s_cancelled` — a confirmed bulk action was declined.
  - `settings_encryption_%s_started` — the UI dispatched a bulk worker.
  - `settings_encryption_%s_completed success=%s backup=%s error_count=%d` — the UI handled
    the domain result while retaining the worker until thread completion.
- **EMERG / ALERT / CRIT / NOTICE / DEBUG**: N/A — no lifecycle condition requires these
  levels, and Python's standard logging configuration does not define NOTICE.

### Log Structure

- Structured logs: yes; stable event prefix followed by `key=value` fields.
- Context: operation, success, error count, backup path where already reported, cleanup bound,
  and concise exception text.
- Log levels used: INFO, WARNING, ERROR.
- Sensitive or large values: settings, environment collections, encryption values, complete
  reports, and error collections are not logged.
- Duplication rationale: worker events diagnose off-thread execution; settings events diagnose
  dispatch and UI outcome handling across the separate domain and lifecycle signals.

## Metrics Implementation

### Performance Metrics

N/A. This is an infrequent, user-initiated desktop maintenance action. The change introduces a
fixed cleanup bound rather than a performance objective, and the section has no metrics
dependency. Adding one would expand the production interface solely for a rare diagnostic.

### Business Metrics

N/A. PYPOST-1072 changes thread ownership only; it does not add a business action or outcome.
Existing start and terminal logs provide sufficient per-execution evidence.

### System Health Metrics

N/A. A cleanup timeout is already a directly actionable WARNING. A dedicated counter would
duplicate this low-frequency event and is not needed to validate bounded suite completion.

## Monitoring Integration

- [ ] Prometheus metrics — N/A; no task-specific metric was warranted.
- [ ] Grafana dashboards — N/A; no new metric or service-level objective.
- [ ] Alerting rules — N/A; no deployment or alerting configuration is in this task's scope.
- [ ] Log aggregation changes — N/A; stable `key=value` events work with existing logging
  handlers and require no new integration.

## Validation Results

- [x] Event formats and logger names inspected in both lifecycle components.
- [x] Cleanup timeout warning asserted exactly with `caplog` at WARNING level.
- [x] Warning-path behavior confirms cleanup stays bounded, ownership clears, and the affected
  button is restored.
- [x] Existing worker ERROR logging remains asserted by the direct worker tests.
- [x] No large data structures or encryption settings are logged.
- [x] Focused lifecycle validation passed: 14 tests in 0.23 seconds.
- [x] Focused `flake8`, Python syntax compilation, and `git diff --check` passed.
- [ ] Metrics collection validation — N/A; no metrics were added.

## Notes

The first validation attempt used the host `pytest` and could not load `PySide6`. The repository
virtual environment was then used with `QT_QPA_PLATFORM=offscreen`; all focused tests passed.
