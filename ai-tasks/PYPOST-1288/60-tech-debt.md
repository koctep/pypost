# PYPOST-1288: Technical Debt Analysis

## Shortcuts Taken

No temporary implementation or architecture shortcut was found. The transport checks its
connected state and Qt's synchronous byte-count result, the controller emits `frame_sent` only
after a complete handoff, and the presenter records the existing outbound counters once for that
signal. This matches the accepted architecture and the requirement that peer receipt is outside
the metric contract.

The controller and Qt adapter each calculate UTF-8 text length. This is a small duplicate
calculation required by their current interfaces; it has no measured performance impact and is
not a blocker. No new metric labels, configuration constants, or hardcoded endpoints were added.

## Code Quality Issues

No code quality issue requiring a change in this task was found. The transport's Boolean result
has one meaning for text and binary sends, and the existing `frame_sent` signal remains the
single counting point for composer, preset, sequence, and presenter fallback sends. The literal
`outbound` is the public metric direction specified by the requirements.

## Missing Tests

The new test module and all affected existing test modules have explicit module-level
`pytest.mark.timeout(30)` markers; there is no timeout-marker blocker. The focused tests cover
accepted non-ASCII text and binary payloads, byte counts, blocked sends, rejected handoffs, and
full, partial, empty, and disconnected Qt adapter returns. The affected `make check` gate passed
as recorded in the Step 5 and Step 6 artifacts.

**NON-BLOCKER — new coverage opportunity:** The metric assertions use a fake transport; they
do not verify counters during a real loopback Qt socket send. The existing loopback test verifies
text and binary transmission but has no presenter metrics assertion. A follow-up could extend
that test to check both outbound counters through the actual adapter, including a zero-byte
message. This is additional integration coverage, not an unmet acceptance criterion.

## Performance Concerns

No measured performance regression or scaling blocker was found. Each accepted send adds two
counter calls and a signal callback. Text length is encoded in the controller and Qt adapter;
optimize that only if large-payload profiling shows a meaningful cost.

## Follow-up Tasks

- **NON-BLOCKER — follow-up:** Add a real loopback Qt WebSocket integration assertion for
  outbound text and binary message and byte counters, including a zero-byte message.
  Jira: [PYPOST-1297](https://pypost.atlassian.net/browse/PYPOST-1297).
- **NON-BLOCKER — pre-existing:** The four malformed-expression nodes below reproduce at base
  commit `aa7f33e07af4`. Existing Jira:
  [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261).
  - `tests/test_function_expression_resolver.py`, class `TestFunctionExpressionResolver`:
    `test_malformed_nested_expressions` and `test_standalone_malformed_closing_paren`.
  - `tests/test_template_service.py`, class `TestTemplateServiceValidationOutcomes`:
    `test_validate_malformed_nested_alignment`.
  - `tests/test_template_service.py`, class `TestTemplateServiceObservability`:
    `test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`.
- **NON-BLOCKER — pre-existing:** The stale PYPOST-1077 dialog inventory node reproduces at
  base commit `aa7f33e07af4`. Existing Jira:
  [PYPOST-1287](https://pypost.atlassian.net/browse/PYPOST-1287).
  - `tests/test_pypost_1077_verification_artifacts.py`:
    `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`.
- **NON-BLOCKER — pre-existing, flaky:**
  `tests/test_websocket_stream_view_repro.py::test_stream_view_transcript_export_actions`
  failed under full-suite load and passed on an isolated rerun. Existing Jira:
  [PYPOST-1286](https://pypost.atlassian.net/browse/PYPOST-1286).
- **NON-BLOCKER — pre-existing:** Full-suite parallel load caused Makefile smoke worker
  timeouts during virtual environment setup. Existing Jira:
  [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262). This is tracked as a
  test-file/worker timeout rather than an individual test assertion failure.

There are no new technical-debt blockers. The developer metrics catalog update remains in
Step 8 as specified by the accepted architecture.
