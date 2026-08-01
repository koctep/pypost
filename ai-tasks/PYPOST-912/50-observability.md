# PYPOST-912: Observability Implementation

## Logging Implementation

### Added Logs

None — production WARNING already landed in PYPOST-875.

### Verified Logs (this ticket)

- **WARNING**:
  - `pypost.agent.lifecycle` —
    `agent_session_failure_dump_hook_failed error=<ExcType>` when the optional
    `__exit__` dump callback raises (now asserted under caplog).

### Log Structure

Unchanged from PYPOST-875:

- Structured event name + scalar `error=<ExcType>`
- Original test failure still propagates after WARNING + shutdown

## Metrics Implementation

N/A — failure-only path; no counters added.

## Monitoring Integration

N/A for test-harness dump path; CI/local logs remain the consumer.

## Validation Results

- [x] Caplog test captures hook-failed WARNING on raising hook
- [x] Original AssertionError propagates
- [x] Catalog entry unchanged in `doc/dev/logging.md` (cross-link added)
- [x] No new log events introduced

## Notes

Authors: grep `agent_session_failure_dump_hook_failed` after a red run, or run
`make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_failure_logs_warning -v"`.
