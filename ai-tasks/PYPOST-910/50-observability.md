# PYPOST-910: Observability Implementation

## Logging Implementation

### Added Logs

None. This task sets explicit Actions `retention-days` on existing
failure artifact uploads and documents the policy. Application /
pytest dump logging remains PYPOST-860.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Log Structure

- Structured logs: N/A (CI retention input only)
- Includes context: docs state 14-day window for downloads
- Log levels: N/A

## Metrics Implementation (if applicable)

### Performance Metrics

No new metrics. Operator note: shorter retention reduces long-lived
artifact storage versus the Actions default window.

### Business Metrics

N/A

### System Health Metrics

N/A

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

(Not applicable — CI retention / docs debt.)

CI surface updated:
- [x] `retention-days: 14` on `agent-e2e` failure upload
- [x] `retention-days: 14` on main `test` matrix failure upload
- [x] Docs note the 14-day window (PYPOST-910)

## Validation Results

Validation results:
- [x] No new application logs required
- [x] No metrics required for DoD
- [x] Large data structures not logged (uploads already-masked dumps)
- [x] Retention policy documented and locked

## Notes

Failure mode for contract drift is the pytest lock
(`tests/test_agent_e2e_ci_failure_retention_doc.py`), not runtime
logging. Upload gating and artifact names from 874/909 unchanged.
