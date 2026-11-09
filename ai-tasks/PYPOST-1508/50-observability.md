# PYPOST-1508: Observability

## Scope

Test-harness call-site ordering only. No new production MCP listen path
changes. Allocate/release DEBUG logs already exist from PYPOST-1546.

## Logging Added

None in this ticket. Existing helpers already emit:

| Location | Level | Event / fields |
| --- | --- | --- |
| `EphemeralPortReserve.allocate` | DEBUG | `ephemeral_ports_allocated host=%s count=%d ports=%s` |
| `EphemeralPorts.release` | DEBUG | `ephemeral_ports_released host=%s count=%d ports=%s` |

## Metrics

N/A — suite-only call-site fix; no Prometheus/OTel counters.

## Validation

- Multi-step hold contract:
  `test_batch_ports_stay_held_across_all_multi_server_setup_steps`.
- Target node:
  `test_process_mode_variable_isolation_under_concurrent_load`.

## Checklist

- [x] No new sensitive data in logs
- [x] Reuse existing DEBUG allocate/release (PYPOST-1546)
- [x] N/A production metrics for this debt fix
