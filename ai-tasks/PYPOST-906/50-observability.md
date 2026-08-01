# PYPOST-906: Observability Implementation

## Logging Implementation

### Added Logs

None. This task only adds `venv-test` as a Make prerequisite of `lint`
(mirroring `typecheck`), updates contract / smoke tests, and will refresh
developer docs in Step 8. No application runtime paths were modified.

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

No new metrics exporters. Operator-visible Make behavior for `make lint`
(and `make check`, which depends on `lint`):

- **First bare visit:** when the test/dev stamp is missing or stale,
  `lint`’s `venv-test` prereq may run `pip install -e ".[dev]"` with
  normal pip stdout, then flake8.
- **Subsequent visits:** when the stamp is current (PYPOST-905 —
  `.venv/.venv-test-<pyver>` vs `pyproject.toml` / marker), Make skips
  the install recipe; lint proceeds to flake8 only.

`run` remains marker-only and is unchanged.

### Business Metrics

N/A

### System Health Metrics

N/A — stamp files under `.venv/` are local build artifacts, not health
probes. This ticket reuses the PYPOST-905 `VENV_TEST_STAMP` path; it does
not add new sentinels.

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
- [x] Operator-visible pip only when stamp recipe runs (via `venv-test`)
- [x] Contract tests assert `lint` prereqs include `venv-test`; bare-venv
      smoke expects ensure-and-succeed

## Notes

Closing the PYPOST-872 lint asymmetry: `make lint` now shares the same
“ensure `[dev]` present” promise as `typecheck` / pytest targets.
Idempotent stamps from PYPOST-905 keep repeated `make lint` / `make check`
cheap when extras are already current. Prefer `make install` once after
clone; first bare `make lint` may still install via `venv-test` if needed.
