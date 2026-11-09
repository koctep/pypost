# PYPOST-1392: Observability Implementation

## Logging Implementation

### Added Logs

Reveal-state persistence builds on MASK-3 logging from PYPOST-1379 and adds
diagnostics for preserve vs reset lifecycle:

- **EMERG**: None (not applicable for GUI presentation components).
- **ALERT**: None (not applicable for GUI presentation components).
- **CRIT**: None (critical runtime errors handled by standard top-level application
  error boundaries).
- **ERR**: None (unparseable JSON bodies continue to fall back to raw text without
  unhandled exceptions).
- **WARNING**: None new for this ticket (async worker failure warnings remain from
  PYPOST-1396).
- **NOTICE**: None (syslog NOTICE mapped to standard Python logging INFO).
- **INFO**: Unchanged from prior MASK-3 / ResponseView lifecycle events
  (`response_view_displayed`, `display_response_skip_pretty_print`).
- **DEBUG**:
  - `pypost/ui/widgets/response_view.py`: `response_masking_preserve_reveal_state` —
    emitted when `display_response(..., preserve_reveal_state=True)` keeps path-keyed
    reveal memory (indent reformat / same-response re-render path).
  - `pypost/ui/widgets/response_mask_controller.py`: `reveal_state_cleared memory_size=<n>` —
    emitted on full `clear()` after wiping `_reveal_state` (new response / `clear_body`).
  - `pypost/ui/widgets/response_mask_controller.py`:
    `reveal_state_spans_cleared memory_size=<n>` — emitted on `clear_spans()` when
    visuals are dropped but reveal memory is retained.
  - `pypost/ui/widgets/response_mask_controller.py`:
    `reveal_state_restored restored_count=<n> memory_size=<n>` — emitted when
    `_apply_persisted_reveals` expands one or more previously revealed paths after a
    reformat.
  - `pypost/ui/widgets/response_mask_controller.py`:
    `response_masking_spans_updated span_count=<n> restored_reveals=<n> memory_size=<n>` —
    extended span-load event now includes restore and memory counts (still no secrets).
  - Existing: `click_to_reveal_toggle path=<path> revealed=<bool>` continues to record
    map writes on user toggles.

### Log Structure

Log format used:

- Structured logs: **yes** (`snake_case_event key=value ...`)
- Includes context: **yes** (`memory_size`, `restored_count`, `restored_reveals`,
  `span_count`, selector `path`, boolean `revealed`)
- Log levels: `DEBUG`, `INFO` (plus existing `WARNING` on async fallback)
- **Zero secret leakage**: counts and paths only; raw/masked token values never logged

## Metrics Implementation (if applicable)

### Performance Metrics

- No new Prometheus/OTel series for persistence bookkeeping (O(spans) restore is
  presentation-local and covered by DEBUG counts).
- Existing response elapsed-time display and UI-thread safety unchanged.

### Business Metrics

- Existing `hidden_value_masks_applied_total{surface="gui_response"}` still incremented
  when masked spans are applied (sync and async). Preserve re-display does not invent a
  new surface label.

### System Health Metrics

- Per-tab `ResponseMaskController` memory size is observable via DEBUG
  `memory_size` fields; full clear on new response / `clear_body` resets the map.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`hidden_value_masks_applied_total{surface="gui_response"}` —
  unchanged)
- [x] OpenTelemetry metrics (unchanged surface counter)
- [ ] Grafana dashboards (central PyPost dashboards; no new panel required)
- [ ] Alerting rules (not required for presentation-state restore)
- [x] Log aggregation (structured syslog-compatible DEBUG/INFO)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`snake_case_event key=value ...`)
- [x] Metrics collection path unchanged and still exercised by masking display
- [x] Logging works on preserve (`set_indent_size`), restore (`set_masked_spans`), and
  clear (`display_response` default / `clear_body`) paths
- [x] Large data structures / secrets are not logged
- [x] Metrics remain available via `MetricsRegistry` / `MetricsOTel`

## Notes

- Preserve logging is intentionally DEBUG-only to avoid noise on routine indent changes.
- STEP 6 remains `[/]` awaiting acceptance gate.
