# PYPOST-1283: Observability Implementation

## Logging Implementation

### Added Logs

- **WARNING**: `pypost/core/mcp_tool_contract.py::validate_environment_overrides` —
  `mcp_env_override_rejected key=<name> reason=<not_overridable|hidden>` emitted
  immediately before raising `McpArgumentValidationError(kind="override_not_permitted")`
  for a caller-supplied MCP argument that targets a real environment-variable name the
  agent is not permitted to override right now. `reason` distinguishes the two secure-
  by-default rejection causes required by this task: `not_overridable` (the key was
  never added to `Environment.mcp_overridable_keys`) vs `hidden` (the key is in
  `mcp_overridable_keys` but Hidden wins and blocks the override anyway). Only the key
  *name* and the boolean-ish reason are logged — never the attempted override value.
  This mirrors the existing `mcp_argument_validation_failed` WARNING already emitted one
  layer up in `pypost/core/mcp_observability.py::record_mcp_validation_failure` (same
  module, same call path, same log level) but adds the reason detail that generic
  handler cannot see, since by the time the exception reaches it only
  `expected_type="override"` remains.
- **INFO**: `pypost/core/mcp_secrets_policy.py::McpSecretsPolicy.apply_permitted_overrides`
  — `mcp_env_override_applied key=<name>` emitted once per environment-variable key that
  an MCP call argument actually overrides (i.e. the key passed the
  `effective_overridable_keys` check: present in `mcp_overridable_keys`, absent from
  `hidden_keys`). Only the key name is logged; the overriding value (which may be a
  secret-shaped value supplied by the calling agent) and the pre-override stored value
  are never logged. This matches the existing INFO-level
  `mcp_param_default_applied method=%s param=%s ...` log in
  `pypost/core/mcp_server_impl.py::_build_execution_variables`, which is the closest
  established precedent for "a per-call value substitution worth an operator's
  attention, at INFO, without the value itself."

Both new logs use `logging.getLogger(__name__)` (module-qualified logger names
`pypost.core.mcp_tool_contract` / `pypost.core.mcp_secrets_policy`), matching every
other module in `pypost/core/`. No new logger configuration was introduced.

### Log Structure

- Structured logs: yes — `key=value`-style single-line messages (`mcp_env_override_rejected
  key=%s reason=%s`, `mcp_env_override_applied key=%s`), consistent with the
  `mcp_argument_validation_failed stage=%s transport=%s tool=%s param=%s
  expected_type=%s` and `mcp_param_default_applied method=%s param=%s
  default_applied=true default_type=%s` conventions already used across
  `pypost/core/mcp_observability.py` and `pypost/core/mcp_server_impl.py`.
- Includes context: yes — key name and rejection reason for denials; key name for
  applied overrides. No secret values, no full argument dicts, no environment-variable
  values are logged (per the "do not log large/secret data" rule and this task's
  explicit no-secret-values instruction).
- Log levels used: WARNING (rejected override attempt — a potential misuse/misconfig
  signal an operator should notice) and INFO (successfully applied override — a normal,
  expected operational event worth a record but not an alert).

## Metrics Implementation (if applicable)

No new metrics were added. The existing MCP metrics pipeline
(`MetricsTrackerProtocol` / `record_mcp_call_outcome` /
`track_mcp_argument_validation_failure`) already captures a rejected override as a
`validation_error` outcome with `expected_type="override"` once
`McpArgumentValidationError` propagates out of `_call_tool_inner` in
`mcp_server_impl.py` and is handled by the existing `except McpArgumentValidationError`
branch, which calls `record_mcp_validation_failure` (tracks
`track_mcp_argument_validation_failure` and the call-outcome/duration metrics). Adding a
second, override-specific metric was judged unnecessary duplication of that existing
signal; the new logs add the missing "which key / which reason" diagnostic detail that
metrics labels intentionally omit (to keep cardinality bounded — env-var names are not
metric label material in this codebase's existing conventions, e.g. `param` values never
appear as metric labels either, only in log lines).

### Performance Metrics

- Not applicable — no new latency-sensitive code path was introduced; override
  enforcement executes as a cheap set-membership check inside the existing preflight
  validation and execution-variable-build paths, both of which are already covered by
  `track_mcp_tool_call_duration`.

### Business Metrics

- Not applicable beyond the existing `validation_error` / `success` outcome counters,
  which already include override rejections under the pre-existing
  `track_mcp_argument_validation_failure` / `record_mcp_call_outcome` metrics.

### System Health Metrics

- Not applicable — this feature has no resource-usage or component-status surface of
  its own.

## Monitoring Integration

- [ ] Prometheus metrics (none added; existing MCP metrics already cover the outcome)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

This repository does not wire its own Prometheus/Grafana/alerting stack in-tree beyond
`MetricsTrackerProtocol`; no change to that integration surface was needed for this
task.

## Validation Results

- [x] Logs are correctly formatted — directly asserted with `unittest.TestCase.assertLogs`
      (the same pattern `tests/test_mcp_server_impl.py` already uses) in
      `tests/test_mcp_tool_contract.py::TestValidateEnvironmentOverrides` (two new tests:
      `test_rejected_hidden_override_logs_warning_with_key_and_reason`,
      `test_rejected_not_overridable_override_logs_warning_with_key_and_reason`) and in
      `tests/test_mcp_secrets_policy.py::TestMcpSecretsPolicy` (two new tests:
      `test_apply_permitted_overrides_logs_info_with_key_not_value`,
      `test_apply_permitted_overrides_does_not_log_for_rejected_keys`). Each test
      captures the emitted record via `captured.output`, checks the exact level
      (`WARNING:` / `INFO:` prefix), checks the literal `key=<name>` (and `reason=<...>`
      for the rejection log) text is present, and asserts the attempted/overriding value
      never appears anywhere in the captured record. Confirmed regression-catching by
      temporarily removing each `logger.warning`/`logger.info` call, re-running these
      tests (all four failed as expected with "no logs ... triggered"), then reverting —
      no production code changed.
- [x] Metrics are collected correctly — no new metrics; existing
      `track_mcp_argument_validation_failure` / `track_mcp_call_outcome` paths are
      unchanged and their tests pass.
- [x] Logging works in error scenarios — the WARNING log fires exactly on the rejection
      path exercised by `tests/test_mcp_environment_override_policy.py`, and is now
      directly asserted (level, key, reason, no-value-leak) by the new
      `tests/test_mcp_tool_contract.py` tests above.
- [x] Large data structures are not logged — only the env-var key name and a short
      reason string are logged; argument values, environment-variable values, and full
      argument dicts are never passed to `logger.*`. This is no longer just a code-
      inspection claim: the new tests assert the attempted/overriding value string is
      absent from the captured log record for both the WARNING and INFO paths.
- [ ] Metrics are available for monitoring — N/A, no new metrics added (existing MCP
      metrics already surface override rejections as `validation_error` outcomes).

## Notes

- Considered adding the WARNING log inside `mcp_observability.py::record_mcp_validation_failure`
  instead (the single existing chokepoint for all `McpArgumentValidationError` cases),
  but that function only has access to `error.expected_type` ("override" for every
  override rejection, whether not-permitted or hidden) — it cannot distinguish "not
  overridable" from "hidden" without either widening `McpArgumentValidationError` with a
  new field (a Step-4 behavior change, out of scope for an observability-only step) or
  duplicating the effective-keys computation. Logging at the true decision point
  (`validate_environment_overrides`, which already computes both `effective` and
  `hidden_set`/`overridable_set`) was simpler and kept the log next to the code that
  knows the reason, without touching the exception's public shape or any caller.
- `mcp_env_override_rejected` is emitted in addition to, not instead of, the existing
  generic `mcp_argument_validation_failed` WARNING in `mcp_observability.py` — the
  caller still sees the generic validation-boundary log with `stage`/`transport`/`tool`
  context; the new log adds the override-specific `reason` detail next to it in the log
  stream.
- Re-ran the full set of tests touching these two modules plus their direct callers
  (`mcp_server_impl`, `mcp_server_registry`, `mcp_proxy_server`,
  `mcp_collection_e2e`, `mcp_server_integration`, `env_presenter`) after the logging
  change; all passed with no regressions (see Worklog / task report for exact counts).
