# PYPOST-915: Observability Implementation

## Logging Implementation

### Added Logs

None — production WARNING already landed in PYPOST-876.

### Verified Logs (this ticket)

- **WARNING**:
  - `pypost.fixtures.agent_e2e_failure` —
    `agent_e2e_failure_artifacts_failed nodeid=… error=OSError` when dump
    write raises `OSError` (now asserted under caplog).
  - Same event with `error=AttributeError` when `ui_snapshot` raises
    `AttributeError` (now asserted under caplog).

### Log Structure

Unchanged from PYPOST-876:

- Structured event name + scalar `error=<ExcType>`
- Original test failure remains primary when dump is invoked from hook

## Metrics Implementation

N/A — failure-only path; no counters added.

## Monitoring Integration

N/A for test-harness dump path; CI/local logs remain the consumer.

## Validation Results

- [x] Caplog tests capture dump-failed WARNING for OSError and AttributeError
- [x] Both paths return `None` (no propagation)
- [x] No new log events introduced

## Notes

Run targeted proof:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_failure_artifacts.py::test_dump_best_effort_on_oserror tests/test_agent_e2e_failure_artifacts.py::test_dump_best_effort_on_attribute_error -v'
```
