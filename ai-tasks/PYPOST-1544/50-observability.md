# PYPOST-1544: Observability Implementation

## Logging Implementation

No new logs were added. No metrics were added. This change tracks wildcard
presence on the breadcrumb. `MaskBreadcrumb` updates a count on push and
pop, and `matches` reads `has_wildcard`. Path segments are not logged.

`JsonSelectorEngine.matches` does not log. The existing compile and redact
DEBUG events stay count-only and unchanged:

- `JsonSelectorEngine._compile` in `pypost/core/json_selector_engine.py`
  logs `json_selector_engine_compiled` with `raw_count`, `bare_keys_count`,
  and `trie_size`. The fields are integer counts. Selector text and path
  segments are omitted.
- `JsonSelectorEngine.redact_tree` in the same module logs
  `json_selector_engine_redact_tree_completed` with `masked_count`. The
  field is an integer count. Selector text, path segments, and field values
  are omitted.

`test_json_selector_engine_observability_and_zero_leak` in
`tests/test_pypost_1394_failing_repro.py` already asserts both event names
and those count fields, and it asserts that fixture secret values stay out
of the records.

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none
- **DEBUG**: none added. The existing compile and redact records above stay
  count-only: `json_selector_engine_compiled` and
  `json_selector_engine_redact_tree_completed`. Path segments are not logged.

### Log Structure

Log format used:

- Structured logs: yes for the existing compile and redact records
  (`event key=value`)
- Includes context: yes for those records (integer counts only). Path
  segments are omitted.
- Log levels: DEBUG only, and only on the existing compile and redact
  records. No level was added for this task.

## Metrics Implementation (if applicable)

No metrics were added.

### Performance Metrics

Added performance metrics:

- **Response time**: none
- **Throughput**: none
- **Error rate**: none

### Business Metrics

Business metrics:

- None added.

### System Health Metrics

System health metrics:

- **Resource usage**: none
- **Component status**: none

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [ ] Logs are correctly formatted
- [ ] Metrics are collected correctly
- [ ] Logging works in error scenarios
- [ ] Large data structures are not logged
- [ ] Metrics are available for monitoring

No new logs or metrics were added, so these checks do not apply. Existing
compile and redact DEBUG events stay count-only. Path segments are not
logged. The 1394 test already asserts those events.

## Notes

This step adds no log line and no metric. Wildcard presence stays on the
breadcrumb and is not written to a log. Production code and tests were left
unchanged. STEP 6 stays `[/]` until the acceptance gate owner marks `[x]`.
