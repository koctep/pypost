# PYPOST-1538: Observability Implementation

## Logging Implementation

No logs were added. No metrics were added. The shared header-selector prefix
is a pure string check. A divergence of that prefix is a failed test
(`tests/test_header_selector_prefix.py`), which is the visible split in
NFR2. Selector text and header names stay out of logs.

`header_selector_name` in `pypost/core/header_selector_prefix.py` has no
logger.

The three call sites:

- `validate_field_selector` in `pypost/core/field_selector_syntax.py` calls
  `header_selector_name` at line 96. The module has no logger. None.
- `sanitize_headers` in `pypost/core/sensitive_text_sanitizer.py` calls
  `header_selector_name` at line 69. That function does not log. None.
  DEBUG records in the same file (lines 97-113) belong to
  `redact_json_response_fields`. They log an exception type name, a
  container type name, and counts. They omit selector text and header names.
  They are not this call site.
- `JsonSelectorEngine._compile` in `pypost/core/json_selector_engine.py`
  calls `header_selector_name` at line 152, then logs. The existing DEBUG
  record is lines 161-168: `json_selector_engine_compiled` with `raw_count`,
  `bare_keys_count`, `path_selectors_count`, and `trie_size`. Those fields
  are integer counts. Header selectors are skipped before the counts (lines
  152-153), so the record omits selector text and header names. It does not
  record that a prefix matched.

No existing log covers the header-prefix match. The `_compile` summary is
the only record on a call site, and it is count-only.

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none
- **DEBUG**: none added. The existing `_compile` record cited above omits
  selector text and header names.

### Log Structure

Log format used:

- Structured logs: yes for the existing `_compile` record (`event key=value`)
- Includes context: yes for that record (integer compile counts only).
  Selector text and header names are omitted.
- Log levels: DEBUG only, and only on the existing `_compile` summary. No
  level was added for this task. The other two call sites do not log.

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

None of these were added or changed. Prefix divergence stays a failed test,
not a new telemetry source.

## Validation Results

Validation results:

- [x] Logs are correctly formatted — no new logs. The existing `_compile`
  record stays `event key=value` and omits selector text and header names.
- [x] Metrics are collected correctly — none were added; nothing new to collect
- [x] Logging works in error scenarios — no new error log. The header-prefix
  path has no error record. `validate_field_selector` and `sanitize_headers`
  stay silent.
- [x] Large data structures are not logged — selector text and header names
  are omitted by `header_selector_name` and by the three call sites
- [x] Metrics are available for monitoring — no new metrics

## Notes

Architecture recorded that this step adds no log line. The caught divergence
is the test in `tests/test_header_selector_prefix.py`. Production code and
tests were left unchanged.
