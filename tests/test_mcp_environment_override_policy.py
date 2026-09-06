"""Red repro tests for PYPOST-1283: MCP environment variable override policy.

Covers the Definition of Done that an MCP tool call may only override an
environment variable when the variable is explicitly marked overridable on
the active `Environment` (`mcp_overridable_keys`) and is not `Hidden`. Today
`MCPServerImpl` has no `overridable_keys_supplier` and no enforcement at all:
a caller-supplied argument matching a bare environment variable name is
merged only into the `mcp.request.*` namespace and never touches the actual
`env_vars` used to render the request, so there is currently no way to even
express "attempted an override" in a way the code checks against permission.

These tests assert the *intended* end state (per `20-architecture.md`):
- an override attempt for a non-overridable variable is rejected with
  `McpArgumentValidationError` before the request executes,
- a variable marked Hidden is never overridable regardless of
  `mcp_overridable_keys` content,
- a permitted override actually flows into the resolved execution variables.

They must fail today because `MCPServerImpl.__init__` does not yet accept an
`overridable_keys_supplier` parameter (planned in `mcp_server_impl.py`
interfaces) — this is the missing feature, not a broken fixture.
"""
from __future__ import annotations

import asyncio
import unittest
from unittest.mock import MagicMock

import pytest

from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.mcp_tool_contract import McpArgumentValidationError
from pypost.core.request_service import ExecutionResult
from pypost.models.models import RequestData
from pypost.models.response import ResponseData

pytestmark = pytest.mark.timeout(30)


def _exec_result(body: str = "ok") -> ExecutionResult:
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


def _stub_request_service(impl: MCPServerImpl) -> MagicMock:
    mock_svc = MagicMock()
    impl._create_request_service = lambda: mock_svc
    return mock_svc


class TestMcpEnvironmentOverridePolicy(unittest.TestCase):
    def test_override_rejected_when_not_marked_overridable(self) -> None:
        """Attempting to override a variable absent from mcp_overridable_keys is rejected."""
        impl = MCPServerImpl(
            variable_supplier=lambda: {"jira_project_key": "ORIGINAL"},
            hidden_keys_supplier=lambda: set(),
            overridable_keys_supplier=lambda: set(),  # nothing overridable
        )
        req = RequestData(
            name="Jira Create Issue",
            expose_as_mcp=True,
            method="GET",
            url="https://jira.example/{{ jira_project_key }}/issue",
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result("must not execute")

        with self.assertRaises(McpArgumentValidationError):
            asyncio.run(
                impl.call_tool(
                    "jira_create_issue", {"jira_project_key": "ATTACKER_PROJ"}
                )
            )

        mock_svc.execute.assert_not_called()

    def test_override_rejected_when_variable_is_hidden(self) -> None:
        """Hidden always wins: overridable+hidden must still be rejected."""
        impl = MCPServerImpl(
            variable_supplier=lambda: {"jira_credentials": "s3cr3t"},
            hidden_keys_supplier=lambda: {"jira_credentials"},
            # Marked overridable, but Hidden must take precedence.
            overridable_keys_supplier=lambda: {"jira_credentials"},
        )
        req = RequestData(
            name="Jira Create Issue",
            expose_as_mcp=True,
            method="GET",
            url="https://jira.example/issue",
            headers={"Authorization": "Bearer {{ jira_credentials }}"},
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result("must not execute")

        with self.assertRaises(McpArgumentValidationError):
            asyncio.run(
                impl.call_tool(
                    "jira_create_issue", {"jira_credentials": "attacker-token"}
                )
            )

        mock_svc.execute.assert_not_called()

    def test_permitted_override_flows_into_execution_variables(self) -> None:
        """A variable marked overridable and not hidden actually overrides at execution."""
        impl = MCPServerImpl(
            variable_supplier=lambda: {"jira_project_key": "ORIGINAL"},
            hidden_keys_supplier=lambda: set(),
            overridable_keys_supplier=lambda: {"jira_project_key"},
        )
        req = RequestData(
            name="Jira Create Issue",
            expose_as_mcp=True,
            method="GET",
            url="https://jira.example/{{ jira_project_key }}/issue",
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result("ok")

        asyncio.run(
            impl.call_tool("jira_create_issue", {"jira_project_key": "OVERRIDDEN"})
        )

        mock_svc.execute.assert_called_once()
        _passed_req, passed_ctx = mock_svc.execute.call_args[0]
        self.assertEqual(passed_ctx.get("jira_project_key"), "OVERRIDDEN")


if __name__ == "__main__":
    unittest.main()
