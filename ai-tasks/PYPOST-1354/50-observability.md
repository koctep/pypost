# PYPOST-1354: Observability Implementation

## Logging Implementation

New diagnostics use stable event prefixes and key/value context through existing Python logging.

| Event | Level | Context | Meaning |
| --- | --- | --- | --- |
| `builtin_paired_environment_derived` | DEBUG | ID, variable/secret counts | Sanitized copy built |
| `workspace_environment_creation_admitted` | INFO | ID, sequence, existing count | Save admitted |
| `workspace_environment_creation_rejected` | INFO | Fixed reason | Teardown, copy pending, or busy |
| `workspace_environment_creation_succeeded` | INFO | ID, sequence, count | Durable publication |
| `workspace_environment_creation_failed` | WARNING | ID, sequence, fixed outcome | Failed/incomplete |
| `builtin_paired_environment_copy_failed` | WARNING | Fixed reason | Template or owner exception |

The derivation event is in `pypost/core/builtin_collections.py`. Canonical creation events are in
`pypost/ui/presenters/env_presenter_creation.py`. Template and owner exceptions are reported in
`pypost/ui/dialogs/mcp_servers_dialog.py` using fixed reason codes.

The negative persistence sequence correlates admission and completion. Publication success is
logged after persistence acknowledgment, rather than after worker dispatch. Rejections never
emit an admission event. Failure uses WARNING because the existing storage worker/presenter
already owns ERROR reporting and the user dialog; no second error dialog was introduced.

New events contain no variable keys or values, environment display names, template contents,
raw exception messages, or tracebacks. Counts identify the operation's size without disclosing
credentials. The UI exception diagnostics never format the exception object.

## Metrics Implementation

No metric schema, protocol method, label set, or dashboard was added. This action uses the
existing environment storage gateway and lifecycle metrics for storage health and bounded drain
outcomes. Structured admission and durable result events supply the copy-specific diagnostic
context. Reusing generic library-operation counters would misclassify a workspace environment
save; a separate business counter is unnecessary for this optional setup action's requirements.

Existing monitoring integration and storage error reporting remain in place. This step does not
claim a new copy-specific latency or throughput metric.

## Validation Results

`make test PYTEST_ARGS='tests/test_mcp_builtin_paired_env.py tests/test_env_presenter.py
 tests/test_environment_storage_gateway.py'` passed all three modules, including all 18 repro
cases. `make lint` passed.

Existing repro assertions were strengthened with `caplog` checks for derivation, teardown
rejection, admission, persistence failure, and successful retry. A candidate with private value
and display-name sentinels plus a credential-like exception sentinel verifies that none appears
in the new creation diagnostics. Failure still publishes no ghost and retry still persists the
copy. The module-level 30-second timeout and bounded worker gates are retained.

The prior full-suite baseline classifications remain unchanged: PYPOST-1298, PYPOST-1299,
PYPOST-1361, and PYPOST-1362. Step 6 remains in progress pending independent acceptance review.
