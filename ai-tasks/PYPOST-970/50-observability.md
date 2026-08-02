# PYPOST-970: Observability Implementation

## Observability Decision

PYPOST-970 is a test-harness DRY migration. It changes no production request, response, wait,
logging, metrics, or user-visible path. The Golden successful Send path now consumes the existing
shared settle helper, which already preserves the same wait telemetry and timeout diagnostics as
the former inline block.

**Decision:** add no production logs or metrics. Reuse the existing `pypost.agent.ui_wait` DEBUG
events and `UiWaitTimeoutError` diagnostic contract. New telemetry would duplicate existing
signals and add operational noise for a test-only ownership change.

## Logging Implementation

### Added Logs

None. No logger call or log level changed.

### Existing Logs Preserved

| Event | Level | Fields | Outcome |
| --- | --- | --- | --- |
| `ui_wait_settled` | DEBUG | `condition`, `waited_ms`, `timeout_s` | Named wait completed |
| `ui_wait_timeout` | DEBUG | `condition`, `waited_ms`, `timeout_s` | Named wait exhausted |

Both events remain emitted by `pypost.agent.ui_wait.wait_until`. Successful Golden settle performs
the same two ordered text waits as before: response status, then response body. A successful wait
uses `condition=text_matches`; a failed status or body wait emits the timeout event before raising.

The log structure remains scalar-only:

- Structured event prefix: yes.
- Context: condition name and timing budget/duration.
- Levels used by this wait path: DEBUG only.
- Response text, expected text, snapshots, and excerpts are not written to these DEBUG logs.

Existing action and fixture events such as `ui_action_applied` and
`agent_e2e_http_stub_installed` are unaffected.

## Timeout Diagnostic Contract

`wait_response_after_send` catches the inner `UiWaitTimeoutError`, captures a failure snapshot,
and re-raises with the Golden binding established in Step 2:

- message prefix: `golden Send settle failed`;
- `timeout_s`: preserved from the failed wait;
- `condition`: preserved (`text_matches` for an ordinary text mismatch);
- inner diagnostics preserved, including `widget_id`, `found`, clipped `expected`, and clipped
  `actual_text`;
- `step`: `wait_response_after_send`;
- `response_excerpt`: bounded response-panel context;
- exception chaining: the wrapper remains chained from the inner wait error.

`response_panel_excerpt` joins response-panel values and retains up to 400 content characters
plus an optional ellipsis; the maximum returned length is 401. If the panel is absent or empty,
it returns an explicit sentinel instead of failing diagnostic collection.

The PYPOST-950 forced-timeout companion remains separate and unchanged. It continues to force an
impossible status with a 50 ms budget and asserts `step`, `response_excerpt`, `widget_id`, and
`expected` evidence.

## Metrics Implementation

### Performance Metrics

No new metric. The migration introduces no new operation and does not change the 15-second shared
settle budget. Existing DEBUG wait events already carry `waited_ms` and `timeout_s` for local or
CI diagnosis.

### Business Metrics

None. A test-helper adoption count is not a product or business outcome and would not be useful in
production monitoring.

### System Health Metrics

None. No resource, process, service, network, or component-health behavior changed.

### No-New-Metrics Rationale

- The changed code runs only in automated tests.
- Status/body wait instrumentation already exists at the shared production wait primitive.
- The acceptance signal is binary CI health under `make test-agent-e2e`.
- Adding counters for a single Golden helper call would increase metric cardinality/maintenance
  without improving incident detection.

## Monitoring Integration

- [ ] New Prometheus metric — not applicable.
- [ ] New Grafana panel — not applicable.
- [ ] New alerting rule — not applicable.
- [ ] New log-aggregation field — not applicable.
- [x] Existing CI monitoring through the Golden tests, AST convention marker, and agent e2e gate.

The operational signal for this ticket is the existing CI test result. No production alert should
fire because a test module changes helper ownership.

## Privacy and Security

- DEBUG wait logs contain timing scalars and a condition name only; they do not contain response
  body values.
- Timeout exceptions can contain clipped expected/actual text and a response excerpt. These are
  failure diagnostics, not automatically emitted production logs.
- The Golden scenario uses deterministic canned fixture content and must not introduce secrets.
- The excerpt retains 400 content characters plus an optional ellipsis; its maximum returned
  length is 401. This size limit is not a redaction guarantee.
- Future scenarios using this helper must keep secrets out of fixtures or sanitize them before
  allowing failure output into CI artifacts.
- Snapshot masking remains unchanged. PYPOST-970 neither expands snapshot capture nor changes
  artifact retention or access.

## Validation Results

No runtime suite was rerun in Step 6. The observability review inspected the changed call, shared
helper, wait primitive, excerpt helper, existing docs, and prior task evidence.

| Validation | Result |
| --- | --- |
| Shared helper keeps inner diagnostics and exception chaining | Confirmed by source inspection |
| Golden passes exact step, message prefix, and current-tab scope | Confirmed by diff inspection |
| DEBUG logs remain timing scalars only | Confirmed in `pypost.agent.ui_wait` |
| Excerpt: 400 content chars plus optional ellipsis; max 401 | Confirmed in helper |
| PYPOST-950 companion remains separate | Confirmed by scoped diff |
| Step 3 AST marker after migration | 1 passed |
| Golden module | 3 passed |
| `make test-agent-e2e` | 109 passed, 1956 deselected, 1 warning |

The acceptance suite is green. Its warning is the existing Starlette/httpx deprecation from
`tests/test_mcp_asgi_compatibility.py`.

## Unrelated Full-Suite Baseline

The completed Step 4 `make test` run reported 2043 passed and one unrelated failure:

```text
tests/test_verify_ai_task_artifacts.py::
TestCommittedBaseline::test_baseline_matches_current_scan
```

The committed task-artifact baseline records 259 violations while the concurrent worktree scan
finds 264. PYPOST-970 remains incomplete and is ignored by that scanner. This baseline drift does
not weaken the Golden observability or agent e2e acceptance evidence.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Golden waits on the wrong tab | Confirm `in_current_tab=True` is still passed |
| Timeout lacks Golden step | Confirm `step="wait_response_after_send"` |
| Timeout lacks useful context | Confirm helper wrapper still sets `response_excerpt` |
| Inner wait evidence disappears | Confirm wrapper merges `exc.diagnostics` before extra fields |
| Expected body never matches | Keep display-form `FIXTURE_BODY_DISPLAY` unchanged |
| Forced companion stops proving timeout | Keep PYPOST-950 inline miss and 50 ms budget separate |
| AST convention marker fails | Confirm scoped import and call in `_golden_fill_send_and_settle` |
| Full suite fails artifact baseline | Reconcile concurrent task artifacts; do not alter Golden |

For a failed Golden settle, inspect the exception in this order:

1. `step` to identify the response-after-Send stage.
2. `widget_id` and `expected` to identify status versus body readiness.
3. `actual_text` to see the last bounded widget value.
4. `response_excerpt` to view bounded response-panel context.
5. DEBUG `ui_wait_timeout` scalars to compare elapsed time with the configured budget.

## Notes

Observability is complete for PYPOST-970 scope. The migration centralizes an existing diagnostic
contract; it does not require new production telemetry, monitoring infrastructure, or privacy
exposure.
