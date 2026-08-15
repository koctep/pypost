# PYPOST-1010: Observability Implementation

## Logging Implementation

### Added Logs

PYPOST-1010 changes only the JSON root selected after existing serializers produce
records. The policy helper is deliberately pure, so it adds no log site that could
duplicate events or expose exported content. The affected export paths already emit
the following safe, structured key-value events, which remain sufficient to diagnose
this change in production:

- **EMERG**: Not applicable. Export-root selection is not a system-wide failure mode.
- **ALERT**: Not applicable. No paging condition is introduced.
- **CRIT**: Not applicable. Export write failures are reported at warning level by
  the user-facing action layer, consistent with existing export behavior.
- **ERR**: Not applicable. No error-level event is needed beyond the existing
  user-visible failure handling.
- **WARNING**: `environment_export_no_selection`, `environment_export_failed`,
  `collection_export_no_selection`, `collection_export_failed`, and
  `collections_export_failed` identify actionable export failures without logging
  serialized records.
- **NOTICE**: Not applicable. Python logging has no project-level NOTICE mapping.
- **INFO**: `environment_export_payload_built`, `environment_export_file_written`,
  `environment_export_completed`, `collection_export_payload_built`,
  `collections_export_payload_built`, `collection_export_file_written`,
  `collection_export_completed`, and `collections_export_completed` record the
  scope, record/request counts, secret-presence flag where relevant, and destination.
- **DEBUG**: Not needed for the one-record-versus-array policy. Logging a payload or
  JSON root would risk exposing collection or environment data, including secrets.

### Log Structure

- Structured logs: yes — stable event names followed by named key-value fields.
- Includes context: yes — counts, safe collection/environment names where already
  present, hidden-value presence, and the selected destination are recorded; the
  JSON payload is never logged.
- Log levels: `INFO`, `WARNING`.

## Metrics Implementation (if applicable)

### Performance Metrics

No export metric was added. The root policy is an in-memory constant-time list-length
check and does not start a request, background operation, or new service boundary.
Adding a new metric interface and plumbing it through UI constructors solely for this
policy would broaden the task without producing a useful production signal.

### Business Metrics

No new business metric applies. Existing Prometheus metrics cover application health
and user interactions independently of this file-shape compatibility fix.

### System Health Metrics

No new system-health metric applies. File-write errors continue through the existing
export error paths and warning logs.

## Monitoring Integration

- [x] Prometheus metrics — existing application integration remains available; no
  PYPOST-1010-specific series is justified.
- [ ] Grafana dashboards — no new metric series.
- [ ] Alerting rules — no new paging condition.
- [x] Log aggregation (ELK, Loki, etc.) — existing standard-library log events can be
  collected by the configured application log handler.

## Validation Results

- [x] Logs are correctly formatted — focused UI tests assert the safe completion
  events for collection and environment exports.
- [x] Metrics are collected correctly — no new metric is required by this pure policy.
- [x] Logging works in error scenarios — existing export actions retain their
  warning-level failure events and user-visible error paths.
- [x] Large data structures are not logged — events contain only counts, flags, names,
  and paths; never serialized JSON records.
- [x] Metrics are available for monitoring — the existing Prometheus registry remains
  available without task-specific changes.

## Notes

The shared `json_root_for_records` helper is intentionally logging-free: its callers
already log safe operation outcomes, while logging the root payload could disclose
exported environment values or collection contents. PYPOST-1011 worktree changes were
not modified or assessed.
