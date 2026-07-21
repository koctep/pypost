# PYPOST-878: Observability Implementation

## Scope

**TEST-HARNESS ONLY.** Extends the existing PYPOST-828 timeout diagnostic
snapshot so `gateway_timeout_detail` passes optional `worker_operation` when
the gateway worker exposes `_operation` (env load/save). **No production
product code was changed.** Production logging, metrics, and monitoring
integration are **N/A**.

The pytest `AssertionError` from `process_until` remains the diagnostic
channel.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key production components | Unchanged (env/collection gateways and workers) |
| Critical path under test | Gateway waits that already use `gateway_timeout_detail` |
| Production logging gap | None |
| Test harness diagnostics | Add load/save label when worker exposes `_operation` |

Critical execution path (test only):

1. Test waits via `process_until(..., timeout_detail=gateway_timeout_detail(gw))`.
2. On timeout: detail now may include `worker_operation=load|save` for env
   workers; collection-style workers still omit the field.

## Logging Implementation

### Added Logs

No new production or harness syslog-style logging.

- **EMERG** / **ALERT** / **CRIT** / **ERR** / **WARNING** / **NOTICE** /
  **INFO** / **DEBUG**: N/A

### Log Structure

- Structured logs: N/A
- Includes context: N/A
- Log levels: none added

### Rationale (no production logging)

Same as PYPOST-828: harness-only triage polish; maintainers read CI pytest
output. Env workers already log `op=` at DEBUG on run start; this ticket does
not duplicate that into production timeout paths.

## Metrics Implementation (if applicable)

### Performance Metrics

None added.

### Business Metrics

None added.

### System Health Metrics

None added.

## Test-side diagnostics (primary observability channel)

| Helper | Change |
| --- | --- |
| `format_storage_async_timeout_detail` | Unchanged (already accepted `worker_operation`) |
| `gateway_timeout_detail` | Passes `getattr(worker, "_operation", None)` when it is a `str` |

Example env gateway timeout fragment:

```text
busy=True pending=True worker_running=True worker_operation=save
```

Collection / load-only style (no `_operation`):

```text
busy=True pending=False worker_running=True
```

### Detail failure safety

Unchanged: detail exceptions never mask the timeout AssertionError.

## Monitoring Integration

- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation — N/A

## Validation Results

- [x] Diagnostic text format verified by unit test
- [x] Collection-style omission verified by unit test
- [x] No large structures logged
- [x] Metrics N/A

## Notes

User documentation N/A. Developer docs updated in Step 8
(`doc/dev/gui_testing.md`, `doc/dev/environment_storage_async.md`).
