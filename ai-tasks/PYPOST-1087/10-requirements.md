# Requirements: PYPOST-1087

## Summary

Revisit the unreachable C2 allowlist rule for `mcp_server_start_failed_ui` in `tests/expected_log_allowlist.yaml` and document its retention as an intentional, forward-looking guardrail rule.

## Background & Motivation

Follow-up F11 from PYPOST-1071 (source item D10):
- In `tests/expected_log_allowlist.yaml:45-51`, the rule for `mcp_server_start_failed_ui` under logger `pypost.ui.presenters.mcp_controls_presenter` was added to satisfy the C2 caplog contract.
- The unit test emitting this error (`tests/test_env_presenter.py:453`) uses `unittest.assertLogs`, which sets `propagate=False` during execution, preventing the ERROR from reaching the root handler inspected by `--log-file` and the CI guardrail.
- The rule is nevertheless valid and necessary when tests or manual executions log to root handlers without `assertLogs`.

## Decision & Requirements

1. Retain the allowlist rule for `mcp_server_start_failed_ui`.
2. Annotate the rule in `tests/expected_log_allowlist.yaml` explicitly noting why it is forward-looking and why `assertLogs` isolates unit-test emission from root handlers.
3. Keep `baseline_error_count: 72` unchanged.
4. Ensure `tests/test_verify_test_log_guardrails.py` continues to pass.
