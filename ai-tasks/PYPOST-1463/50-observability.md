# PYPOST-1463: Observability Implementation

## Logging Implementation

The accepted process transaction already includes the necessary production events:

- **INFO** `mcp_registry_process_reconfigured instance_id=...` records accepted replacement.
- **WARNING** `mcp_registry_process_reconfigure_rejected` records public instance identity,
  lifecycle phase, and `restored`/`cleaned` outcomes for a rejected change.
- **INFO** `mcp_registry_status` records identity, lifecycle state, and whether a message exists.
  Status messages provide an operator-visible failure category without copying exception text.
- Existing supervisor spawn/stop/exit events identify the child and bounded reclamation outcome.

Events use stable prefixes and meaningful key/value fields. Rejection remains a warning because
it is a handled configuration operation; failed restoration also publishes a failed status.
No runtime values, credentials, tools, large payloads, or raw exception messages are added to
these transaction events. Step 6 retains the existing logs rather than duplicating them.

## Metrics Implementation

Every transaction status update calls `_publish_instance_metrics`, which updates the existing
`mcp_server_instances{state}` Prometheus gauge through `set_mcp_server_instance_counts`.
The bounded states are `starting`, `running`, `failed`, and `stopped`; a rejected change that
recovers returns to running, while failed restoration is counted as failed.

No new metric is required for this lifecycle correction. Existing aggregate state counts and
structured transaction outcomes cover health and diagnosis without per-instance label growth.
Process request throughput and resource monitoring remain within their existing scopes.

## Monitoring Integration

The existing Prometheus metrics integration receives status counts through the registry's
metrics protocol. Existing application logging receives the transaction events. This task
introduces no dashboard, alert rule, or external telemetry configuration.

## Validation Results

- Added caplog contracts to existing real-process commit and rejected-candidate tests.
- Successful changes assert the INFO event and targeted public identity.
- Rejected candidates assert the WARNING event and successful restoration/cleanup fields.
- A secret-bearing injected exception is absent from captured logs.
- Existing registry metric tests cover state-count publication; behavioral cases assert
  running/failed outcomes and completion signals as primary acceptance criteria.
- `make -o lint-tests lint` passes production Python, Markdown, and relative-link checks.
- `make test WORKERS=1` with `PYTEST_ARGS` selecting
  `tests/test_mcp_process_reconfigure_repro.py tests/test_mcp_server_registry.py -q`
  passes both files (27.43 seconds). Evidence: `/tmp/PYPOST-1463-step6-tests.log`.

## Notes

The pre-existing test-lint violation at `tests/test_mcp_server_registry.py:308` remains tracked
as [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509). No production code changed
during this step; new assertions validate the logging introduced with the transaction.
