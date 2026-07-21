# PYPOST-887: Observability Implementation

## Logging Implementation

### Added Logs

None. `_discard_chunk_buffer` is intentional silent lifecycle cleanup: it only
stops a pending flush timer and drops buffered chunks. Emitting DEBUG/INFO on
every discard would noise normal finish / error / re-send paths without aiding
diagnosis of the double-body race (which is covered by regression tests).

Existing presenter logs already bookend the request lifecycle (no body content):

- **INFO** `request_finished` — `method`, `status_code`, `elapsed_time`, `size`
  (`tabs_presenter_worker._on_request_finished`, immediately after discard)
- **INFO** `request_cancelled` / **ERR** `request_error` — error path after discard
- **INFO** `request_send_initiated` — new send after `clear_body` + discard
- **DEBUG** `stale_worker_cleared` — unrelated stale-worker guard (PYPOST-401)

Do **not** log chunk text or buffer contents (sensitive / large payloads).

### Log Structure

Log format used:
- Structured logs: yes (existing `key=value` logger style)
- Includes context: n/a for this change (no new statements)
- Log levels: no new log statements

## Metrics Implementation (if applicable)

### Performance Metrics

N/A. No Prometheus / presenter metric exists for chunk-buffer flush or discard.
Existing finish metric is unchanged:

- `track_response_received(method, status_code)` in `_on_request_finished`

Adding a discard counter would not map to a user-facing or ops alert and is out
of scope for this race fix.

### Business Metrics

None.

### System Health Metrics

None.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — no change
- [ ] Grafana dashboards — no change
- [ ] Alerting rules — no change
- [ ] Log aggregation — no change

## Validation Results

Validation results:
- [x] No new logs required (existing finish/error/send logs suffice)
- [x] Large data structures are not logged (discard stays silent by design)
- [x] Metrics N/A for chunk discard (no similar presenter event metrics)
- [x] Race covered by `tests/test_tabs_presenter_response_display.py`

## Notes

If field reports of double body recur after this fix, prefer a single DEBUG when
a non-empty buffer or live timer is discarded (`had_timer`, `buffered_chunks`
count only — never body text), not a permanent INFO on every request.
Prior art for “no new logs”: `ai-tasks/PYPOST-831/50-observability.md`.
