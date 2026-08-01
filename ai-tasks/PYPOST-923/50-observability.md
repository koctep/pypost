# PYPOST-923: Observability Implementation

## Analysis

This task restores CI hygiene on `dev`: refreshed dependency locks, aligned
license inventory, and Qt/EGL apt parity for `make-install-smoke`. Changes are
Makefile targets, committed lock/CSV artifacts, workflow YAML, and a pytest
workflow-contract test. No application runtime paths, request handlers, or
product logging surfaces were introduced or modified.

**Runtime application logging: N/A** — justified by Step 6 rule scope (key
operations / critical execution paths). Those paths are CI gates and committed
supply-chain artifacts, not in-process PyPost services.

## Logging Implementation

### Added Logs

None. Existing Makefile / script / GitHub Actions output is unchanged in
behavior; only inputs (locks, CSV, apt env) were refreshed or mirrored.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A (gate failures remain non-zero exits + CI job logs)
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A (no new application INFO events)
- **DEBUG**: N/A

### Log Structure

- Structured logs: no (CI/tooling stdout/stderr only)
- Includes context: yes — job name, `diff` / inventory `--check` messages,
  pytest failure for missing Qt apt packages in the contract test
- Log levels: N/A for application; Actions job status is the operator signal

## Metrics Implementation (if applicable)

### Performance Metrics

Not added. Operator note: smoke job duration may change slightly once
collection succeeds (suite actually runs); that is Actions timing, not a
product metric.

### Business Metrics

N/A

### System Health Metrics

N/A as product metrics. CI health signals for this ticket:

| Signal | Where |
| --- | --- |
| Dev lock freshness | `check-lock-dev` job / `make check-lock-dev` |
| Prod lock + inventory | `check-license-inventory` / `make check-license-inventory` |
| Smoke Qt env parity | `make-install-smoke` apt step; contract test |
| Contract drift | `tests/test_ci_make_install_smoke_qt_runtime.py` |

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

(Not applicable — ephemeral GitHub Actions jobs; no production service.)

CI surface (unchanged pattern, restored green):
- [x] `check-lock-dev` fails with compile/diff output on stale `requirements-dev.txt`
- [x] `check-license-inventory` fails on CSV vs lock drift
- [x] `make-install-smoke` provisions the same Qt/EGL apt set as `test` /
  `agent-e2e`
- [x] Fast pytest contract asserts smoke-job apt parity without live Actions

## Validation Results

Validation results:
- [x] Logs are correctly formatted (N/A — no new application logs)
- [x] Metrics are collected correctly (N/A — no new metrics)
- [x] Logging works in error scenarios (N/A — gate stderr / pytest asserts)
- [x] Large data structures are not logged (N/A)
- [x] Metrics are available for monitoring (N/A — Actions job status)

## Notes

- Failure mode for smoke Qt drift is the contract test, not runtime logging
  (same pattern as PYPOST-874 / PYPOST-861 workflow contracts).
- Supply-chain observability improves indirectly: committed lock and
  `LICENSES/transitive.csv` diffs show pin/inventory movement on review.
- No changes required to `doc/dev/logging.md` or application log catalogs.
