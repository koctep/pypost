# PYPOST-905: Observability Implementation

## Logging Implementation

### Added Logs

None. This task only adds Make stamp files for `venv-test` /
`venv-otel`, contract tests, and developer docs. No application runtime
paths were modified.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Log Structure

- Structured logs: N/A
- Includes context: N/A
- Log levels: N/A

## Metrics Implementation (if applicable)

### Performance Metrics

No new metrics exporters. Operator-visible Make behavior:

- **Skip when current:** second `make venv-test` / `venv-otel` (or
  pytest targets with stamps already valid) prints no `pip install`
  recipe — Make reports nothing to do for the stamp file.
- **Install when needed:** missing or stale stamp (vs `pyproject.toml` /
  marker) still runs `pip install -e ".[dev]"` / `".[otel]"` with normal
  pip stdout on the recipe.

### Business Metrics

N/A

### System Health Metrics

N/A — stamp files under `.venv/` (`.venv-test-<pyver>`,
`.venv-otel-<pyver>`) are local build artifacts, not health probes.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

(Not applicable — build tooling debt.)

## Validation Results

Validation results:
- [x] No new application logs required
- [x] No metrics required for DoD
- [x] Large data structures not logged (N/A)
- [x] Pip install stdout still appears only when stamp recipes run
- [x] Contract tests assert skip vs install via combined Make output

## Notes

Idempotent stamps close the dual-install tax noted in PYPOST-872
observability. Prefer `make install` once after clone (touches both
stamps); repeated `make test` then skips redundant pip when
`pyproject.toml` is unchanged.
