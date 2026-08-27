# PYPOST-1196: Observability Implementation

## Logging Implementation

### Added Logs

No new production log event names were added. Existing restart-path events
remain the contract:

- **INFO**: `mcp_tools_changed tool_count=%d restarting=true` — exposed-set
  change triggers restart
- **WARNING**: `mcp_port_still_busy host=%s port=%d` — bindable wait deadline
  while the prior port is still occupied
- **INFO**: `mcp_server_listening host=%s port=%d` — successful listen after
  (re)start
- **ERROR**: `mcp_server_start_failed host=%s port=%d message=%s` — bind /
  startup failure (including EADDRINUSE after a still-busy port)

Behavioral change affecting observability: `_wait_until_port_bindable` default
budget is **10.0s** (was 5.0s), so under slow teardown the WARNING is less
likely; when it still fires, meaning is unchanged.

### Log Structure

- Structured logs: yes (event name + key=value fields)
- Includes context: `host`, `port`, `tool_count`, `message` as applicable
- Log levels: INFO / WARNING / ERROR (unchanged vocabulary)

## Metrics Implementation (if applicable)

### Performance Metrics

None added — not required for this debt fix.

### Business Metrics

None added.

### System Health Metrics

None added.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation-compatible structured lines (existing)

## Validation Results

Validation results:

- [x] `mcp_port_still_busy` still emitted on deadline (Step 3 red path before fix)
- [x] Happy-path restart reaches `mcp_server_listening` without `start_failed`
- [x] Docs updated for 10s wait / join-timeout retain (Step 8)

## Notes

Keep-thread-on-join-timeout does not emit a new event; `is_running()` remaining
true during residual teardown is the control. Catalog rows in
`doc/dev/logging.md` for `mcp_port_still_busy` stay valid.
