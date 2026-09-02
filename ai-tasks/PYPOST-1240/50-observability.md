# PYPOST-1240: Observability Assessment

## Affected Diagnostic Surface

This change affects the message text emitted by the ownership-validation tests in
`tests/test_display_role_scan_ownership.py`. The two affected missing-responsibility
assertions are:

- Missing `find_tree_index_by_display_text`: the diagnostic identifies the Tree Index module and
  directs the maintainer to restore recursive lookup.
- Missing `_select_item_view`: the diagnostic identifies the UI Actions module and directs the
  maintainer to restore item-view selection.

The messages are presented through the existing `AssertionError` and pytest failure output. They
are consumed by local maintainers and CI quality-gate results; this task does not introduce a new
diagnostic channel or alter the ownership-validation decision.

## Logging, Metrics, and Tracing Assessment

### Production Logging

No production logs are needed. The change is limited to test-side, source-inspection assertion
messages. It does not execute a new application operation, handle a new runtime error, or change
the behavior of `pypost.agent.tree_index` or `pypost.agent.ui_actions`. Adding runtime logs would
add noise without providing operational visibility into a production path.

### Metrics

No production metrics are needed. There is no changed request path, throughput, latency, error
rate, business event, or system-health condition. The relevant signal remains whether the existing
ownership validation passes or reports an assertion failure in the local/CI quality gate.

### Tracing and Telemetry

No tracing or telemetry is needed. The diagnostic is synchronous test output from an existing
validation boundary, with no distributed operation, external dependency, or production workflow
whose execution needs correlation.

## Preserved Reporting Behavior

- Ownership detection, lookup behavior, selection behavior, and application-facing behavior remain
  unchanged.
- Successful validation continues to report success through the existing test and quality-gate
  flow.
- The existing `AssertionError`/pytest reporting path remains the presentation mechanism.
- Only the two targeted messages gain owner and remedy context; unrelated ownership diagnostics
  retain their existing wording and ordering.
- When multiple ownership conditions fail, the existing aggregation and source-order reporting are
  preserved; each targeted condition remains independently actionable.
- Pytest assertion rewriting may append its normal explanation, but the explicit diagnostic text
  keeps the missing responsibility, owner, and remedy together on one readable line.

## Validation and Evidence

Evidence reviewed for this assessment:

- `10-requirements.md` defines the change as diagnostic communication only and requires no
  application-runtime behavior change.
- `20-architecture.md` explicitly identifies the existing quality-gate diagnostic as the affected
  observability surface and states that no production logging, metrics, tracing, or telemetry is
  required.
- `40-code-cleanup.md` records that the current diff is limited to the ownership-diagnostic tests,
  with no production-code changes.
- The focused source-inspection repros verify that each actionable one-line diagnostic names its
  symbol, owner, and remedy.

Validation commands for this artifact:

- `make verify-ai-tasks` — passed.
- `make lint` — passed.

## Operational Troubleshooting Guidance

When the ownership quality gate reports one of these diagnostics:

1. Use the named responsibility and owner in the one-line failure to select the repair area.
2. For a recursive/tree lookup failure, inspect `pypost/agent/tree_index.py` and restore
   `find_tree_index_by_display_text` and its recursive lookup responsibility.
3. For an item-view selection failure, inspect `pypost/agent/ui_actions.py` and restore
   `_select_item_view` and its item-view selection responsibility.
4. Re-run the existing focused ownership-validation test, then the normal repository quality gate.

No production dashboard, alert, log aggregation query, trace lookup, or runtime feature flag is
needed to troubleshoot this condition. If a CI system displays only a truncated assertion, inspect
the complete pytest failure output so the explicit one-line diagnostic is visible.

## Explicitly Out of Scope

The following observability work is intentionally excluded from PYPOST-1240:

- Runtime logging in `pypost.agent.tree_index` or `pypost.agent.ui_actions`.
- New counters, histograms, health checks, dashboards, alerts, or SLO instrumentation.
- Distributed tracing, correlation IDs, telemetry events, or log-aggregation integration.
- Changes to production error reporting, exception types, ownership rules, lookup algorithms,
  selection behavior, or aggregate validation semantics.
- Rewording unrelated diagnostics or creating a new diagnostic service/API.
- Changes to production code, tests, or the task roadmap as part of Step 6.

## Conclusion

The existing test failure output is sufficient observability for this message-only ownership-test
diagnostic change. The two messages are actionable in local and CI quality-gate results, and no
additional production instrumentation is warranted.
