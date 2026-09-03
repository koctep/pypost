# PYPOST-1100: Technical Debt Analysis

## Shortcuts Taken

- The MCP SDK handler is registered with `validate_input=False`. Validation was
  moved into the application boundary so callers receive a safe, parameter-specific
  diagnostic instead of SDK-generated text. This preserves the published schema,
  but couples required-name and type-validation behavior to the application adapter
  and requires parity checks when the SDK is upgraded.
- Validation intentionally runs in two stages: preflight uses the agent-visible
  parameter view, and the HTTP execution boundary validates effective values after
  defaults are applied. This preserves hidden-variable and legacy-default behavior,
  but means parameter specifications are resolved more than once per HTTP call.
- The optional WebSocket `stop_when` parameter is retained by inserting a fixed
  `string` declaration into the resolver. This keeps the existing probe contract,
  but the parameter metadata is hardcoded rather than defined by a shared protocol
  declaration.
- The existing 325-line `mcp_server_impl.py` cap was preserved by moving helpers
  into adjacent modules. The implementation still reaches the cap, so future MCP
  transport or observability additions will need further decomposition.

## Code Quality Issues

- Runtime compatibility checks and JSON Schema construction are separate sources of
  truth. A future supported-type or integer-string grammar change must update both
  paths and their tests.
- `MCPServerImpl._call_tool_inner()` still coordinates lookup, transport-specific
  specification resolution, validation, dispatch, exception handling, and outcome
  recording. It is readable within the current cap, but additional behavior should
  be extracted into transport adapters before this method grows again.
- The HTTP preflight resolver and the execution-boundary validator independently
  discover template variables. Caching a resolved call specification at tool
  registration, with invalidation when definitions change, would reduce duplication
  and lower drift risk.
- The new validation counter is implemented across Prometheus, OpenTelemetry, the
  null tracker, and Qt delegation, but dashboards and alerting rules are not part of
  this change. Operators must currently discover useful thresholds themselves.

## Missing Tests

- Streamable HTTP has an end-to-end safe-error assertion, but the equivalent invalid
  call path through legacy SSE is not covered directly.
- The WebSocket integration test proves one invalid declared value does not start a
  probe. A transport matrix covering all seven declared types, defaults, and safe
  diagnostics for WebSocket would reduce parity risk.
- Boundary tests do not yet exercise JSON-number edge cases such as non-finite
  floating-point values or very large values. Their acceptance should be specified
  explicitly if direct callers can bypass JSON decoding.
- If a resolved or reused tool-specification cache is introduced, add a test that it
  remains correct after a registered request definition is mutated or replaced.
- Timeout audit: every changed pytest module has an explicit module-level timeout:
  `tests/test_mcp_tool_contract.py` (30s), `tests/test_mcp_server_impl.py` (60s),
  `tests/test_mcp_server_integration.py` (120s),
  `tests/test_websocket_mcp_probe_repro.py` (30s), and
  `tests/test_mcp_validation_observability.py` (60s). No timeout blocker was found.

## Performance Concerns

- Normal validation is linear in the supplied argument and declared-parameter
  counts, so its expected cost is small. HTTP calls additionally scan templates and
  construct parameter maps during preflight and again at the execution boundary.
  This is the main avoidable per-call overhead and should be measured before adding
  caching.
- Every rejected call records a warning, a bounded metric, a response-duration
  metric, and an activity entry. The activity log is bounded, but sustained invalid
  traffic can still create logging and metric volume; rate limiting or aggregation
  may be needed if validation failures become noisy.

## Follow-up Tasks

- Consolidate the runtime predicate and published schema generation around one
  contract definition, including shared tests for all supported types.
- Add legacy SSE and broader WebSocket transport-matrix tests for invalid values,
  required names, defaults, no-dispatch behavior, and safe observability.
- Measure template-spec resolution cost and consider a registration-time cache with
  an explicit invalidation policy.
- Define and publish dashboard or alert thresholds for
  `mcp_argument_validation_failures_total` and the `validation_error` outcomes.
- Decompose `MCPServerImpl` further and centralize the WebSocket `stop_when`
  declaration if more transport-specific MCP parameters are added.
- The task-introduced snapshot changes record `mcp_server_impl.py` at 325 lines
  (up from 314) and `metrics_tracking.py` at 145 lines (up from 140). Their existing
  caps remain 325 and 145; revisit both sizes with the next MCP or metrics refactor.

### Baseline failures

The following are `NON-BLOCKER — pre-existing` and are tracked by Jira
`PYPOST-1261`. They reproduce in the task-base evidence or are the documented flaky
Qt baseline cluster; no duplicate Jira follow-up issue was created.

The remaining `template_service.py` snapshot mismatch is pre-existing PYPOST-1261
debt: the current file has 260 lines while the snapshot records 241. It is distinct
from the task-introduced MCP and metrics snapshot changes documented above.

- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::`
  `test_malformed_nested_expressions` — expected `invalid_argument`, received
  `invalid_arity`.
- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::`
  `test_standalone_malformed_closing_paren` — expected `invalid_argument`, received
  `invalid_arity`.
- `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::`
  `test_validate_malformed_nested_alignment` — expected `invalid_argument`, received
  `invalid_arity`.
- `tests/test_template_service.py::TestTemplateServiceObservability::`
  `test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
  — expected the `invalid_argument` metric code, received `invalid_arity`.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::`
  `test_markdown_snapshot_matches_current_metrics` — the pre-existing
  `template_service.py` snapshot records 241 lines while the current file has 260.
- `tests/test_environment_list_widget.py::<module>` — flaky parallel-worker Qt
  SIGSEGV, exit `-11`; individual node attribution is unavailable.
- The PYPOST-1100 base-commit probe also recorded the flaky file-level node
  `tests/test_env_dialog.py::<module>`: exit `-11` after all 51 tests passed, while
  an unchanged-tree focused rerun passed. This is the same unresolved Qt
  process/teardown class of failure; individual node attribution is unavailable.
