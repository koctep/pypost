# PYPOST-1550: Observability Implementation

## Logging Implementation

No new logs were added. No metrics were added. This task adds only the
characterization tests in
`tests/test_pypost_1550_medium_indent_preserve.py`. Production behavior
already holds. Parent `ai-tasks/PYPOST-1392/50-observability.md` already
names the preserve DEBUG event. The generation-mismatch return already
logs both generation numbers. A second log on those paths would repeat
the same facts. Production modules were not edited.

Preserve. An indent change on a longer response calls
`ResponseView.set_indent_size`, which redisplays the same response with
`preserve_reveal_state=True`. That path emits:

- DEBUG `reveal_state_spans_cleared` with `memory_size` (map kept) from
  `ResponseMaskController.clear_spans`.
- DEBUG `response_masking_preserve_reveal_state` from
  `ResponseView.display_response` (no extra fields).
- DEBUG `response_masking_worker_dispatched` with `generation`, `chars`,
  and `selectors_count` when the body is in the medium range.
- DEBUG `response_mask_worker_completed` from `ResponseMaskWorker.run`
  with `generation`, `spans`, and `duration` when formatting finishes.
- DEBUG `response_masking_async_completed` with `generation` and
  `span_count` when the completion generation matches
  `_mask_format_generation`.
- DEBUG `reveal_state_restored` with `restored_count` and `memory_size`,
  only when at least one path is still true (a value left revealed).
- DEBUG `response_masking_spans_updated` with `span_count`,
  `restored_reveals`, and `memory_size`. `restored_reveals` counts only
  paths stored as true, so a value left hidden is not expanded.

Dropped stale completion. `_on_mask_formatting_completed` returns before
`setText` and `set_masked_spans` when `generation` differs from
`_mask_format_generation`. That return already emits DEBUG
`response_masking_worker_stale_result_ignored` with `generation` and
`current_generation` only. The newer display and its reveal choices stay
in place. The matching failure return emits DEBUG
`response_masking_worker_stale_failure_ignored` with the same two
generation fields. This ticket's late completion is the result path.

None of these lines include secret values, response bodies, or revealed
field text. Fields are generation numbers, integer counts, or a
duration.

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none added. Existing `response_view_displayed` stays a
  display lifecycle line (`status`, `size`, `format`) and does not
  record reveal memory or generation.
- **DEBUG**: none added. Preserve is
  `response_masking_preserve_reveal_state` in
  `ResponseView.display_response`, plus `reveal_state_spans_cleared`,
  `response_masking_worker_dispatched`,
  `response_mask_worker_completed`, `response_masking_async_completed`,
  `reveal_state_restored` for paths still true, and
  `response_masking_spans_updated` (`restored_reveals` counts true
  paths only). A dropped stale completion is
  `response_masking_worker_stale_result_ignored` in
  `ResponseView._on_mask_formatting_completed`, with `generation` and
  `current_generation` only.

### Log Structure

Log format used:

- Structured logs: yes for the existing records (`event key=value`)
- Includes context: yes (generation numbers and counts). Secret values,
  response bodies, and revealed field text are omitted.
- Log levels: DEBUG on the events above. INFO remains on the existing
  display lifecycle line. No level was added for this task.

## Metrics Implementation (if applicable)

No metrics were added. The existing counter
`hidden_value_masks_applied_total` with surface `gui_response` is
unchanged. A stale completion returns before that counter is
incremented. A current completion still increments it when spans are
applied, as before.

### Performance Metrics

Added performance metrics:

- **Response time**: none. Worker completion already logs `duration` on
  DEBUG `response_mask_worker_completed`.
- **Throughput**: none
- **Error rate**: none

### Business Metrics

Business metrics:

- None added.

### System Health Metrics

System health metrics:

- **Resource usage**: none
- **Component status**: none added. Reveal-map size stays visible on
  the existing DEBUG `memory_size` fields. Generation mismatch stays
  visible on `generation` and `current_generation`.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

No new series and no new dashboard. The existing mask-applied counter
and the syslog-compatible DEBUG lines stay as prior tickets left them.

## Validation Results

Validation results:

- [x] Logs are correctly formatted
- [ ] Metrics are collected correctly
- [ ] Logging works in error scenarios
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring

Reviewed `ResponseView.set_indent_size`, `display_response`, and
`_on_mask_formatting_completed`, plus `ResponseMaskWorker.run` and
`ResponseMaskController.clear_spans`, `set_masked_spans`, and
`_apply_persisted_reveals`. Templates stay `event key=value` with
counts or generation numbers. Production code was not edited, so
`make lint` and `make test` were not run. Metric checks do not apply
because no metric was added. The stale return is a DEBUG drop, not a
new error path.

## Notes

This step adds no log line and no metric. Preserve and a dropped stale
completion are already diagnosed by the DEBUG events listed above.
STEP 6 stays `[/]` until the acceptance gate owner marks `[x]`.
