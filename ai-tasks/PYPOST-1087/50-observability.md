# Observability: PYPOST-1087

## Overview

Audited observability implications of the allowlist rule for `mcp_server_start_failed_ui`.

## Findings

- The rule in `tests/expected_log_allowlist.yaml` matches `logger: pypost.ui.presenters.mcp_controls_presenter` with `message_prefix: mcp_server_start_failed_ui`.
- `baseline_error_count` remains 72.
- The rule protects against CI test failures whenever this ERROR is captured by `--log-file`.
