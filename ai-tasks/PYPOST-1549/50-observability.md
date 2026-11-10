# PYPOST-1549: Observability Implementation

## Logging Implementation

No new logs were added. No metrics were added. This task adds only the
characterization tests in `tests/test_pypost_1549_clear_and_remask.py`.
Production behavior already holds. Parent
`ai-tasks/PYPOST-1392/50-observability.md` already requires the clear
and preserve DEBUG events below, and those call sites already emit
them. A second log on the same paths would repeat the same facts.

Clear-reset. `ResponseView.clear_body` calls
`ResponseMaskController.clear`. After the map is wiped, `clear` emits
DEBUG `reveal_state_cleared` with `memory_size` set to the size before
the wipe. The next `display_response` keeps the default
`preserve_reveal_state=False`, so it calls `clear` again and emits the
same event with `memory_size=0`. New spans start masked.
`set_masked_spans` then emits DEBUG `response_masking_spans_updated`
with `restored_reveals=0` and `memory_size=0`. `reveal_state_restored`
is not emitted when nothing is expanded.

Re-mask persistence. Hiding a revealed value writes false through
`handle_click`, which emits DEBUG `click_to_reveal_toggle` with `path`
and `revealed=False`. Indent calls `set_indent_size`, which redisplays
the same response with `preserve_reveal_state=True`. That path emits:

- DEBUG `reveal_state_spans_cleared` with `memory_size` (map kept).
- DEBUG `response_masking_preserve_reveal_state` (no extra fields).
- DEBUG `reveal_state_restored` with `restored_count` and
  `memory_size`, only when at least one path is still true (a value
  left revealed).
- DEBUG `response_masking_spans_updated` with `span_count`,
  `restored_reveals`, and `memory_size`. `restored_reveals` counts only
  paths stored as true, so a re-masked field is not expanded. A field
  never revealed has no toggle line and is not expanded.

None of these lines include secret values, response bodies, or revealed
field text. `path` is the selector path. `revealed` is a boolean. The
other fields are integer counts.

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none added. Existing `response_view_displayed` stays a
  display lifecycle line (`status`, `size`, `format`) and does not
  record reveal memory.
- **DEBUG**: none added. Clear-reset is
  `reveal_state_cleared` in `ResponseMaskController.clear` (called from
  `ResponseView.clear_body` and from a later `display_response` that
  does not preserve), plus `response_masking_spans_updated` with
  `restored_reveals=0`. Re-mask persistence is
  `click_to_reveal_toggle` (`revealed=False`),
  `response_masking_preserve_reveal_state` in
  `ResponseView.display_response`, `reveal_state_spans_cleared`,
  `reveal_state_restored` for paths still true, and
  `response_masking_spans_updated` (`restored_reveals` counts true
  paths only).

### Log Structure

Log format used:

- Structured logs: yes for the existing records (`event key=value`)
- Includes context: yes (counts, or `path` and `revealed`). Secret
  values, response bodies, and revealed field text are omitted.
- Log levels: DEBUG on the events above. INFO remains on the existing
  display lifecycle line. No level was added for this task.

## Metrics Implementation (if applicable)

No metrics were added. The existing counter
`hidden_value_masks_applied_total` with surface `gui_response` is
unchanged and is not a reveal-memory signal.

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
- **Component status**: none added. Reveal-map size stays visible on
  the existing DEBUG `memory_size` fields.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

No new series and no new dashboard. The existing mask-applied counter
and the syslog-compatible DEBUG lines stay as PYPOST-1392 left them.

## Validation Results

Validation results:

- [x] Logs are correctly formatted
- [ ] Metrics are collected correctly
- [ ] Logging works in error scenarios
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring

Reviewed the existing calls in `ResponseView.clear_body`,
`ResponseView.display_response`, `ResponseView.set_indent_size`, and
`ResponseMaskController.clear`, `clear_spans`, `set_masked_spans`,
`_apply_persisted_reveals`, and `handle_click`. Templates stay
`event key=value` with counts, or `path` and `revealed`. Production
code was not edited, so `make lint` and `make test` were not run.
Metric checks do not apply because no metric was added. This ticket
adds no error path. Unparseable JSON still falls back without a new
log.

## Notes

This step adds no log line and no metric. Clear-reset and re-mask
persistence are already diagnosed by the PYPOST-1392 DEBUG events
listed above. STEP 6 stays `[/]` until the acceptance gate owner marks
`[x]`.
