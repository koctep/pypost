# PYPOST-1543: Observability Implementation

## Logging Implementation

No new logs were added. No metrics were added. Dropping the stored
compiled-rule list removes the deleted list length from compile debug.
The compile debug log already reports `trie_size`. Selector text is not
logged.

The live path already emits two DEBUG records:

- `JsonSelectorEngine._compile` in `pypost/core/json_selector_engine.py`
  logs `json_selector_engine_compiled` with `raw_count`,
  `bare_keys_count`, and `trie_size`. The record is unchanged except the
  removed `path_selectors_count` field. The fields are integer counts.
  Selector text is omitted.
- `JsonSelectorEngine.redact_tree` in the same module logs
  `json_selector_engine_redact_tree_completed` with `masked_count`. This
  record is unchanged. The field is an integer count. Selector text and
  field values are omitted.

`test_json_selector_engine_observability_and_zero_leak` in
`tests/test_pypost_1394_failing_repro.py` already asserts both event names
and those count fields, and it asserts that fixture secret values stay out
of the records. `test_compile_debug_reports_trie_size_without_list_length`
in `tests/test_pypost_1543_failing_repro.py` asserts `trie_size` and the
absence of `path_selectors_count`.

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none
- **DEBUG**: none added. Existing records:
  `json_selector_engine_compiled` (unchanged except the removed
  `path_selectors_count` field; still reports `trie_size`) and
  `json_selector_engine_redact_tree_completed` (unchanged). Both omit
  selector text.

### Log Structure

Log format used:

- Structured logs: yes for the existing live-path records
  (`event key=value`)
- Includes context: yes for those records (integer counts only). Selector
  text is omitted. `path_selectors_count` is no longer a compile field.
- Log levels: DEBUG only, and only on the existing live-path records. No
  level was added for this task.

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

No new logs or metrics were added, so these checks do not apply. Compile
debug reports `trie_size` and no longer reports the deleted list length.
The redact debug event is unchanged. Selector text stays out of both
records.

## Notes

This step adds no log line and no metric. The compile event
`json_selector_engine_compiled` and the redact event
`json_selector_engine_redact_tree_completed` stay as they are, except
`path_selectors_count` was removed from compile debug. Production code
and tests were left unchanged. STEP 6 stays `[/]` until the acceptance
gate owner marks `[x]`.
