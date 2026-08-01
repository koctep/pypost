# PYPOST-943: Observability Implementation

## Analysis

This task fixes the slow Makefile install smoke **test seed contract** so an
isolated workspace satisfies setuptools dynamic metadata from committed
`pyproject.toml`. Changes are pytest helpers and a fast seed-contract test only
— no application runtime paths, request handlers, or product logging surfaces
were introduced or modified.

**Runtime application logging: N/A** — justified by Step 6 rule scope (key
operations / critical execution paths). Those paths are CI gates and test
fixtures, not in-process PyPost services.

## Logging Implementation

### Added Logs

None. Existing Makefile / pip / GitHub Actions output is unchanged in
behavior; only the isolated-workspace seed content was corrected.

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
- Includes context: yes — job name, pytest traceback, assertion messages with
  missing seed paths or `make install` stderr
- Log levels: N/A for application; Actions job status is the operator signal

## Metrics Implementation (if applicable)

### Performance Metrics

Not added. Operator note: `make-install-smoke` job duration is unchanged in
structure (network-heavy editable install); Actions timing is not a product
metric.

### Business Metrics

N/A

### System Health Metrics

N/A as product metrics. CI / test health signals for this ticket:

| Signal | Where |
| --- | --- |
| Isolated install success | `make-install-smoke` job; `TestSlowInstallSmoke` |
| Packaging/seed drift | `tests/test_makefile_install_seed_contract.py` (fast, default `make test`) |
| Install subprocess failure | `_run_make` captures stderr; asserted on non-zero exit |
| Post-install env sanity | Slow test runs `.venv/bin/python -c "import pydantic"` |

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

(Not applicable — ephemeral GitHub Actions jobs; no production service.)

CI surface (unchanged pattern, restored green after seed fix):
- [x] `make-install-smoke` runs `pytest tests/test_makefile.py -m slow -v --tb=short`
- [x] Main `test` job excludes `@pytest.mark.slow`; seed-contract test runs in fast matrix
- [x] Fast seed-contract test fails with explicit missing artifact paths before any network install
- [x] Slow smoke failure surfaces setuptools/pip stderr via `assert result.returncode == 0, result.stderr`

## Validation Results

Validation results:
- [x] Logs are correctly formatted (N/A — no new application logs)
- [x] Metrics are collected correctly (N/A — no new metrics)
- [x] Logging works in error scenarios (N/A — gate stderr / pytest asserts)
- [x] Large data structures are not logged (N/A)
- [x] Metrics are available for monitoring (N/A — Actions job status)

## Notes

- Failure mode for packaging/seed drift is the **fast seed-contract test** in
  default CI, not waiting for the slow network install (same contract-testing
  pattern as PYPOST-923 workflow YAML tests).
- Prior failure signature (`ModuleNotFoundError: No module named 'pypost'` during
  dynamic version resolution) is visible in CI logs and local `make test-slow`
  stderr; the fix prevents recurrence by copying `pypost/version.py` and
  `README.md` into the isolated workspace.
- Local visibility: `make test-slow` for slow install smoke; `make test` includes
  the seed-contract guard without network.
- No changes required to `doc/dev/logging.md` or application log catalogs.
