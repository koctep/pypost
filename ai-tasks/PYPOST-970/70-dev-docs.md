# PYPOST-970: Developer Documentation

## Documentation Scope

PYPOST-970 changes test-harness ownership, not production or user-visible behavior. The minimum
canonical developer documentation was updated in:

- `doc/dev/agent_e2e_send_settle.md`
- `doc/dev/agent_golden_e2e.md`

No user documentation, public API documentation, configuration reference, or release note is
needed.

## Changes Made

### Shared Send-settle guide

`agent_e2e_send_settle.md` now records Golden as a shared-helper consumer instead of an inline
wait exception. It documents:

- status-before-body sequencing on `RESPONSE_STATUS` and `RESPONSE_BODY`;
- Golden's `in_current_tab=True` binding;
- the preserved `golden Send settle failed` prefix and `wait_response_after_send` step;
- the inherited `SEND_SETTLE_TIMEOUT_S` 15-second default;
- preservation of the original wait condition, timeout, diagnostics, and exception chain;
- the separate PYPOST-950 forced-timeout companion and why it remains inline;
- focused convention/diagnostic commands and the complete agent e2e command;
- troubleshooting for wrong-tab matches, diagnostic drift, and the intentional forced miss.

### Golden E2E guide

`agent_golden_e2e.md` now describes and demonstrates the actual successful Send path:

1. click Send in the current request tab;
2. call `wait_response_after_send` with current-tab scoping;
3. observe expected status first and display-form body second;
4. preserve Golden's diagnostic prefix, step, excerpt, and inner wait evidence on timeout.

The architecture table, flow diagram, usage example, scenario steps, timeout table, focused
validation commands, and troubleshooting table were aligned with that behavior. The guide also
states that the PYPOST-950 companion intentionally uses an impossible inline status wait with a
50 ms budget because it proves the failure contract rather than the successful settle contract.

## Configuration

No new configuration was added. Golden omits the helper's `timeout` argument and therefore uses
the existing 15-second `SEND_SETTLE_TIMEOUT_S` default for each ordered text wait. The module's
60-second `pytest-timeout` marker remains unchanged.

## Validation

Focused commands were run with explicit pytest timeout budgets:

```text
make test-agent-e2e \
  PYTEST_ARGS="tests/test_agent_e2e_response_panel.py::test_golden_success_send_uses_shared_settle_helper --timeout=10 -q"
make test-agent-e2e \
  PYTEST_ARGS="tests/test_agent_golden_e2e.py::test_agent_golden_settle_timeout_includes_step_and_excerpt --timeout=60 -q"
```

Results:

| Check | Result |
| --- | --- |
| Golden shared-helper adoption marker | 1 passed in 0.02s |
| PYPOST-950 forced-timeout diagnostics | 1 passed in 0.49s |
| Developer-doc relative links | Existing canonical targets confirmed |
| `git diff --check` | Passed |

The complete agent e2e gate was not rerun in Step 8. Step 4 already recorded 109 passed, 1956
deselected, and one existing warning; Step 8 changed Markdown only.

## Review Status

Step 8 remains `[/]` pending documentation review. It must not be marked `[x]` until approval.
