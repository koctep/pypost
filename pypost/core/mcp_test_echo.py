"""Test-only MCP variable echo helpers for process-isolation suites."""
from __future__ import annotations

import json
import os

from pypost.core.request_service import ExecutionResult, ResponseData


def maybe_echo_execution_variables(
    variables: dict[str, str],
) -> ExecutionResult | None:
    """Return an echo ExecutionResult when PYPOST_MCP_TEST_ECHO_VARS=1.

    Child worker processes cannot observe parent-process RequestService mocks
    after spawn. Isolation tests set this env gate so tool calls return the
    current variable snapshot without live HTTP.

    Keys avoid sensitive-name heuristics (e.g. ``secret``) so values survive
    MCP response sanitization.
    """
    if os.environ.get("PYPOST_MCP_TEST_ECHO_VARS") != "1":
        return None
    body = json.dumps(
        {
            "server_index": variables.get("server_index"),
            "isolation_marker": variables.get("unique_secret"),
            "resolved_id": variables.get("server_id"),
        }
    )
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={"content-type": "application/json"},
            body=body,
            elapsed_time=0.0,
            size=len(body),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )
