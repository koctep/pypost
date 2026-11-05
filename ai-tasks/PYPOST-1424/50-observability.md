# PYPOST-1424: Observability Implementation

## Logging Implementation

### Added Logs

- **INFO**: `collection_variable_manifest_discovery_started gen=%d` — dialog starts
  background catalog discovery
- **INFO**: `collection_variable_manifest_discovery_completed gen=%d entry_count=%d` —
  discovery finished and combo entries are ready to append
- **INFO**: `collection_variable_manifest_discovery_cancelled gen=%d` — user cancelled
  discovery via loading Cancel
- **WARNING**: `collection_variable_manifest_discovery_stale_discarded` /
  `…_error_stale_discarded` — generation mismatch discard
- **WARNING**: `collection_variable_import_library_populate_failed error=%s` — preserved
  event name for discovery failure (same as prior sync path)
- **DEBUG**: worker started / completed / cancelled / interrupted /
  interrupted_on_error under `ManifestDiscoveryWorker`
  (`collection_variable_manifest_discovery_worker_*`)

### Log Structure

Log format used:
- Structured logs: yes (key=value fields)
- Includes context: yes (generation id, entry_count, error)
- Log levels: DEBUG, INFO, WARNING

## Metrics Implementation (if applicable)

### Performance Metrics

No new Prometheus/OTel counters in this change. Discovery duration can be inferred from
started/completed log timestamps if needed later.

### Business Metrics

None added.

### System Health Metrics

None added.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted
- [x] Logging works in error scenarios (discovery_failed path)
- [x] Large data structures are not logged (only entry_count)
- [ ] Metrics are collected correctly — N/A
- [ ] Metrics are available for monitoring — N/A

## Notes

Fetch-path log events (`collection_variable_remote_fetch_*`) unchanged.
Retry of discovery reuses `_on_retry_fetch` when no library selection is active.
