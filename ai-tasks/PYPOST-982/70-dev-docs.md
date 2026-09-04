# PYPOST-982: Developer Documentation Assessment

## Decision

**Update required and completed.** The task adds a POST-path companion to the
existing Mapping multi-URL E2E settle-timeout coverage. The existing developer
HTTP fixture guide documented the happy-path POST Send and the GET timeout
companion, but it did not identify the POST timeout test, its exact diagnostic
step name, or its focused invocation.

The targeted update to `doc/dev/agent_e2e_http.md` now records the POST
companion alongside the GET companion, the inventory gate's GET/POST coverage,
the exact `wait_response_after_mapping_post_send` diagnostic step, the shared
`FORCED_SETTLE_TIMEOUT_S` policy, and the focused Make command.

## Documentation Assessment

Reviewed the following developer guidance against the accepted PYPOST-982
requirements, architecture, implementation, cleanup, observability, and debt
artifacts:

- `doc/dev/agent_e2e_http.md` — updated because the Mapping module inventory
  and timeout-companion guidance omitted the new POST companion.
- `doc/dev/agent_e2e_send_settle.md` — remains accurate for the shared
  `wait_response_after_snapshot` API, bounded forced timeout, and diagnostic
  wrapping contract.
- `doc/dev/agent_golden_e2e.md` — remains accurate for the sibling Golden
  forced-timeout pattern; no Golden behavior changed.
- `doc/dev/agent_e2e.md` — remains accurate as the umbrella E2E harness guide;
  no new public harness API or lifecycle rule was introduced.
- `doc/dev/testing.md` and `doc/dev/parallel_test_runner.md` — remain accurate
  for Make-based E2E/test execution and explicit test timeout expectations.

No update to the runner or umbrella documentation is needed. Duplicating the
method-specific inventory outside `agent_e2e_http.md` would make the guidance
harder to maintain without adding developer value.

## Exact Test Contract Documented

- Test: `test_mapping_post_send_settle_timeout_includes_step_and_excerpt`
- Module: `tests/test_agent_e2e_http_mapping_multi_url.py`
- Settle helper: `wait_response_after_snapshot`
- Forced budget: `FORCED_SETTLE_TIMEOUT_S` (`0.05` seconds)
- Diagnostic step: `wait_response_after_mapping_post_send`
- Diagnostic excerpt: non-empty string in `diagnostics["response_excerpt"]`
- Inventory gate: `test_mapping_multi_url_settle_timeout_companion_exists`

## Scope

Changed only:

- `doc/dev/agent_e2e_http.md`
- `ai-tasks/PYPOST-982/70-dev-docs.md`

No source, test logic, `AGENTS.md`, sprint registry, protected baseline,
roadmap status, or unrelated file was changed. No commit was created.

## Validation

Validation is limited to repository Make targets:

- `make lint`
- `make verify-ai-tasks`
- POST companion:

  ```text
  mapping_module=tests/test_agent_e2e_http_mapping_multi_url.py
  post_timeout=test_mapping_post_send_settle_timeout_includes_step_and_excerpt
  make test-agent-e2e \
    PYTEST_ARGS="${mapping_module}::${post_timeout} -q"
  ```

- Inventory gate:

  ```text
  inventory_module=tests/test_agent_e2e_http.py
  inventory_test=test_mapping_multi_url_settle_timeout_companion_exists
  make test \
    PYTEST_ARGS="${inventory_module}::${inventory_test} -q"
  ```

## Work Estimate

Estimated token usage: 6,500 tokens.
