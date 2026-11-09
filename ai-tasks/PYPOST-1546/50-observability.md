# PYPOST-1546: Observability

## Scope

Test-harness only (no production MCP listen path changes). Logging is for
diagnosing residual port-reservation flakes under parallel `make test`.

## Logging Added

| Location | Level | Event / fields |
| --- | --- | --- |
| `tests/helpers/port_allocation.py` `EphemeralPortReserve.allocate` | DEBUG | `ephemeral_ports_allocated host=%s count=%d ports=%s` |
| `tests/helpers/port_allocation.py` `EphemeralPorts.release` | DEBUG | `ephemeral_ports_released host=%s count=%d ports=%s` |

No large payloads or credentials are logged (host, counts, port integers only).

## Metrics

N/A — test helper; no Prometheus/OTel counters added for suite-only allocation.

## Validation

- Hold/release contract exercised by
  `test_reserve_ephemeral_ports_holds_exclusively_against_reuseaddr_thief`.
- Successful allocate/release paths stay quiet at INFO/WARNING (DEBUG only).

## Checklist

- [x] Structured context on allocate/release (host, count, ports)
- [x] No sensitive data in logs
- [x] N/A production metrics for this debt fix
