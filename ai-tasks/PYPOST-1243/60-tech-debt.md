# PYPOST-1243: Technical Debt Analysis

## Scope Reviewed

Reviewed the shared autocomplete implementation, query-parameter and request-header table
integration, multiline body editor integration, MCP compatibility exports, metrics and logging
changes, focused tests, and the Step 1–6 artifacts.

## Blocker Analysis

The two Step 7 acceptance blockers have been resolved within the existing task scope.

- **RESOLVED — solid-audit baseline drift:** autocomplete metric delegation remains on the
  `MetricsManager` public API through `MetricsTrackingMixin`, while `metrics.py` is within
  the existing 70-line cap. The baseline snapshot records the resulting line count.
- **RESOLVED — legacy autocomplete logging:** the shared implementation retains structured
  application events and emits the legacy trigger/selection message shapes on the historical
  logger. Trigger prefixes and selected variable names are included for compatibility;
  resolved values and request payloads remain excluded.
- Changed pytest modules declare explicit timeout markers (`60` seconds for GUI tests and
  `30` seconds for metrics tests), so the mandatory timeout requirement is satisfied.
- Completion candidates, inserted references, feedback, metric labels, and logs use variable
  names or bounded context only; resolved values and sensitive values are not exposed.
- The latest `make test` run produced five failed files: `tests/test_environment_list_widget.py`
  and `tests/test_main_window_alert_reload.py` ended in unrelated Qt crashes;
  `tests/test_mcp_server_headers_table.py` retained a legacy logging expectation that conflicts
  with the redaction contract; and the two `tests/test_solid_audit_baseline.py` failures are the
  blocker above. The first three are non-blockers for this task but require separate Jira
  follow-ups; no Jira keys were supplied in the existing artifacts.

## Shortcuts Taken

- The shared delegate discovers names through optional parent attributes instead of requiring
  every host to implement the declared provider protocol. This reduced integration churn but
  weakens static contract checking.
- Feedback is stored as host state/tooltips and status metrics rather than introduced as a
  dedicated reusable status-widget component.
- Body popup positioning is anchored to the editor's bottom-left rather than the current cursor
  rectangle; this is adequate for the current feature but is not a complete editor UX solution.

## Code Quality Issues

- `CodeEditor` and `VariableAwareTableWidget` each implement overlapping completion and feedback
  logic. A future extraction should centralize parsing, candidate selection, status publication,
  and metric instrumentation behind one host adapter API.
- `mcp_server_headers_table.py` retains the old autocomplete class implementations under private
  names even though the public names now re-export the shared classes. They are dead migration
  code and increase maintenance and review cost.
- The shared module and host adapters rely on several untyped or loosely typed status and result
  boundaries. Introducing explicit return aliases and typed feedback collections would improve
  static verification without changing behavior.

## Missing Tests

- The focused tests exercise the completion contract and host methods, but do not fully drive a
  real query/header table edit transaction through Qt's delegate lifecycle and model commit.
- Body completion tests do not verify popup placement near different cursor lines, focus changes,
  or multiline keyboard/mouse interaction end to end.
- Compatibility tests confirm the MCP import surface but do not cover all legacy constructor and
  delegate behavior through the re-exported implementation.
- No test currently verifies that repeated environment refreshes preserve an already-open editor's
  cursor and popup selection state.

## Performance Concerns

- Candidate filtering sorts or scans the complete variable-name collection during popup updates.
  This is acceptable for current environments; large-environment optimization is explicitly
  deferred to PYPOST-1244.
- Reference feedback rescans edited host text and table value cells on updates. Very large body
  documents or tables may make this synchronous work noticeable.

## Deferred or Related Work

- PYPOST-1244: candidate limits and large-environment performance.
- PYPOST-1245: theme and popup styling centralization.
- PYPOST-1246: platform, focus, and IME integration coverage.
- Separate Jira follow-ups should reconcile the three unrelated full-suite failures listed in the
  blocker analysis and update their test contracts or fixtures as appropriate.

## Follow-up Tasks

1. Consolidate body and table completion/status behavior into the shared host contract.
2. Remove the private legacy autocomplete implementations after compatibility usage is confirmed.
3. Add delegate lifecycle, body popup geometry, focus/IME, and repeated-refresh regression tests.
4. Create or link Jira issues for the three unrelated full-suite failures before addressing them;
   they are non-blockers for PYPOST-1243.

## Validation

- `make lint` — passed.
- `make typecheck` — passed (`189` known baseline errors).
- `make verify-ai-tasks` — passed after the artifact update.
- `make test` — prior run: 311 passed, 4 skipped, 5 failed; the unrelated failures remain
  listed above and the two task-caused blockers are resolved.

Step 7 remains in progress (`[/]`) pending the acceptance gate.
