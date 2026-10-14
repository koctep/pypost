"""Tests for permanent MCP output masking of hidden response fields (PYPOST-1378).

Validates that RequestData.hidden_response_fields are permanently masked ('***')
in agent-visible MCP tool responses across root, nested, and array paths while
preserving in-memory ResponseData immutability, passing non-JSON safely through,
and ensuring no reveal tools or parameters exist in the MCP schema.
"""

from __future__ import annotations

import json
import logging
import unittest
from unittest.mock import MagicMock

import pytest
from mcp.types import TextContent

from pypost.core.mcp_server_impl import (
    MCPServerImpl,
    format_structured_tool_result,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.request_service import ExecutionResult
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.models import RequestData
from pypost.models.response import ResponseData

pytestmark = pytest.mark.timeout(60)


def _exec_result(
    body: str = "ok",
    logs: list[str] | None = None,
    script_error: str | None = None,
    status_code: int = 200,
) -> ExecutionResult:
    """Create a mock ExecutionResult with authentic ResponseData."""
    execution_error = None
    if script_error:
        execution_error = ExecutionError(
            category=ErrorCategory.SCRIPT,
            message="Post-script execution failed.",
            detail=script_error,
        )
    return ExecutionResult(
        response=ResponseData(
            status_code=status_code,
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=logs or [],
        execution_error=execution_error,
    )


def _stub_request_service(impl: MCPServerImpl, mock_svc: MagicMock | None = None) -> MagicMock:
    """Replace per-call RequestService factory with a mock."""
    mock_svc = mock_svc or MagicMock()
    impl._create_request_service = lambda: mock_svc
    return mock_svc


def _parse_envelope(content: TextContent) -> dict:
    """Parse outer MCP TextContent JSON envelope."""
    return json.loads(content.text)


def _parse_body(content: TextContent) -> dict | list:
    """Parse inner response body JSON from MCP TextContent envelope."""
    envelope = _parse_envelope(content)
    return json.loads(envelope["body"])


class TestMcpHiddenResponseFieldsMasking(unittest.IsolatedAsyncioTestCase):
    """Test suite for permanent MCP output masking of hidden response fields."""

    async def test_mcp_output_masks_single_and_multiple_root_fields(self):
        """Root-level configured fields are masked with '***' while others remain intact."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Get Customer",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/customers/1",
            hidden_response_fields=["tax_id", "ssn"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                {
                    "tax_id": "99-9999999",
                    "ssn": "000-11-2222",
                    "username": "alice",
                    "id": 42,
                }
            )
        )

        out = await impl.call_tool("get_customer", {})
        self.assertEqual(len(out), 1)
        body = _parse_body(out[0])

        self.assertEqual(body["tax_id"], "***")
        self.assertEqual(body["ssn"], "***")
        self.assertEqual(body["username"], "alice")
        self.assertEqual(body["id"], 42)

    async def test_mcp_output_masks_nested_object_fields(self):
        """Nested dictionary selectors (dot notation and key selectors) mask child values."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Get User Profile",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/profile",
            hidden_response_fields=[
                "user.token",
                "metadata.credentials.secret",
                "profile.account_number",
            ],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                {
                    "user": {"token": "usr_tok_123", "name": "Bob"},
                    "metadata": {
                        "credentials": {
                            "secret": "cred_sec_789",
                            "role": "admin",
                        }
                    },
                    "profile": {
                        "account_number": "ACC-555",
                        "email": "bob@example.com",
                    },
                }
            )
        )

        out = await impl.call_tool("get_user_profile", {})
        body = _parse_body(out[0])

        self.assertEqual(body["user"]["token"], "***")
        self.assertEqual(body["user"]["name"], "Bob")
        self.assertEqual(body["metadata"]["credentials"]["secret"], "***")
        self.assertEqual(body["metadata"]["credentials"]["role"], "admin")
        self.assertEqual(body["profile"]["account_number"], "***")
        self.assertEqual(body["profile"]["email"], "bob@example.com")

    async def test_mcp_output_masks_fields_in_array_of_objects(self):
        """Array wildcard and child selectors mask matching fields in every array element."""
        impl = MCPServerImpl()
        req = RequestData(
            name="List Accounts",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/accounts",
            hidden_response_fields=["items[*].password", "items[*].account_id"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                {
                    "items": [
                        {
                            "id": 1,
                            "password": "pass1",
                            "account_id": "acc-101",
                            "name": "Item A",
                        },
                        {
                            "id": 2,
                            "password": "pass2",
                            "account_id": "acc-102",
                            "name": "Item B",
                        },
                    ]
                }
            )
        )

        out = await impl.call_tool("list_accounts", {})
        body = _parse_body(out[0])

        self.assertEqual(body["items"][0]["password"], "***")
        self.assertEqual(body["items"][0]["account_id"], "***")
        self.assertEqual(body["items"][0]["name"], "Item A")
        self.assertEqual(body["items"][1]["password"], "***")
        self.assertEqual(body["items"][1]["account_id"], "***")
        self.assertEqual(body["items"][1]["name"], "Item B")

    async def test_mcp_output_masks_root_level_array_of_objects(self):
        """Top-level JSON array of objects masks configured fields in each item."""
        impl = MCPServerImpl()
        req = RequestData(
            name="List Clients",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/clients",
            hidden_response_fields=["client_id"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                [
                    {"client_id": "c1", "name": "Alice"},
                    {"client_id": "c2", "name": "Bob"},
                ]
            )
        )

        out = await impl.call_tool("list_clients", {})
        body = _parse_body(out[0])

        self.assertIsInstance(body, list)
        self.assertEqual(body[0]["client_id"], "***")
        self.assertEqual(body[0]["name"], "Alice")
        self.assertEqual(body[1]["client_id"], "***")
        self.assertEqual(body[1]["name"], "Bob")

    async def test_mcp_output_masks_non_string_values(self):
        """Non-string field values (ints, booleans, objects, arrays) are replaced with '***'."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Get Config",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/config",
            hidden_response_fields=["pin", "is_admin", "auth_matrix", "codes"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                {
                    "pin": 12345,
                    "is_admin": True,
                    "auth_matrix": {"level": 3, "super": True},
                    "codes": [10, 20, 30],
                    "username": "charlie",
                }
            )
        )

        out = await impl.call_tool("get_config", {})
        body = _parse_body(out[0])

        self.assertEqual(body["pin"], "***")
        self.assertEqual(body["is_admin"], "***")
        self.assertEqual(body["auth_matrix"], "***")
        self.assertEqual(body["codes"], "***")
        self.assertEqual(body["username"], "charlie")

    def test_format_structured_tool_result_honors_hidden_response_fields(self):
        """format_structured_tool_result accepts and applies hidden_response_fields."""
        res = _exec_result(
            body=json.dumps(
                {
                    "tax_id": "99-999",
                    "billing_ref": "REF-123",
                    "status": "active",
                }
            )
        )
        output_text = format_structured_tool_result(
            res,
            hidden_response_fields=["tax_id", "billing_ref"],
        )
        envelope = json.loads(output_text)
        body = json.loads(envelope["body"])

        self.assertEqual(body["tax_id"], "***")
        self.assertEqual(body["billing_ref"], "***")
        self.assertEqual(body["status"], "active")

    async def test_mcp_output_non_json_body_passes_through(self):
        """Plain text or HTML body passes through safely without crash or alteration."""
        impl = MCPServerImpl()
        raw_html = "<html><body><h3>502 Bad Gateway</h3></body></html>"
        req = RequestData(
            name="Get Status Page",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/status",
            hidden_response_fields=["tax_id", "pin"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(body=raw_html, status_code=502)

        out = await impl.call_tool("get_status_page", {})
        envelope = _parse_envelope(out[0])

        self.assertEqual(envelope["status"], 502)
        self.assertEqual(envelope["body"], raw_html)

    async def test_mcp_output_malformed_json_fallback(self):
        """Malformed JSON payload safely passes through without JSONDecodeError crash."""
        impl = MCPServerImpl()
        malformed = '{"key": "broken json value...'
        req = RequestData(
            name="Broken Endpoint",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/broken",
            hidden_response_fields=["tax_id"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(body=malformed)

        out = await impl.call_tool("broken_endpoint", {})
        envelope = _parse_envelope(out[0])

        self.assertEqual(envelope["body"], malformed)

    async def test_mcp_output_empty_body_passes_through(self):
        """Empty HTTP 204 response body returns empty string without error."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Empty Resource",
            expose_as_mcp=True,
            method="DELETE",
            url="http://api.example.com/resource/1",
            hidden_response_fields=["tax_id"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(body="", status_code=204)

        out = await impl.call_tool("empty_resource", {})
        envelope = _parse_envelope(out[0])

        self.assertEqual(envelope["status"], 204)
        self.assertEqual(envelope["body"], "")

    async def test_mcp_output_unmatched_fields_remain_intact(self):
        """Fields not matching any selector remain completely unaltered."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Get Metrics",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/metrics",
            hidden_response_fields=["non_existent_field"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                {
                    "public_id": "pub_123",
                    "score": 98.6,
                    "active": True,
                }
            )
        )

        out = await impl.call_tool("get_metrics", {})
        body = _parse_body(out[0])

        self.assertEqual(body["public_id"], "pub_123")
        self.assertEqual(body["score"], 98.6)
        self.assertTrue(body["active"])

    async def test_underlying_response_data_not_mutated(self):
        """Underlying ResponseData in ExecutionResult remains unmutated in memory."""
        impl = MCPServerImpl()
        raw_body = json.dumps(
            {
                "tax_id": "99-999",
                "secret_key": "topsecret_123",
                "public_name": "Acme Corp",
            }
        )
        req = RequestData(
            name="Get Company Info",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/company",
            hidden_response_fields=["tax_id", "secret_key"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        exec_res = _exec_result(body=raw_body)
        mock_svc.execute.return_value = exec_res

        out = await impl.call_tool("get_company_info", {})
        self.assertEqual(len(out), 1)

        # In-memory execution result response body must still have authentic raw content
        self.assertEqual(exec_res.response.body, raw_body)
        self.assertIn("99-999", exec_res.response.body)
        self.assertIn("topsecret_123", exec_res.response.body)

    async def test_mcp_list_tools_contains_no_unmask_parameters(self):
        """Generated tool input schemas never expose reveal/unmask parameters."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Secure Endpoint",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/data",
            hidden_response_fields=["tax_id"],
        )
        impl.register_tools([req])
        tools = await impl.list_tools()
        self.assertEqual(len(tools), 1)

        props = tools[0].inputSchema.get("properties", {})
        forbidden_names = {
            "unmask",
            "reveal",
            "reveal_secrets",
            "show_hidden",
            "raw",
            "reveal_masked",
            "unmask_secret",
        }
        for name in forbidden_names:
            self.assertNotIn(
                name,
                props,
                f"Tool schema must not expose forbidden unmask parameter '{name}'",
            )

    async def test_mcp_server_registers_no_reveal_tools(self):
        """MCPServerImpl does not register auxiliary tools to reveal or unmask data."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Normal Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/normal",
            hidden_response_fields=["tax_id"],
        )
        impl.register_tools([req])
        tools = await impl.list_tools()
        registered_names = {tool.name for tool in tools}

        for name in registered_names:
            self.assertFalse(
                name.startswith(("reveal", "unmask", "get_raw")),
                f"Registered tool '{name}' must not be a reveal or unmask tool",
            )

    async def test_mcp_call_tool_ignores_or_rejects_unmask_argument(self):
        """Unmask arguments passed by callers cannot bypass permanent redaction."""
        impl = MCPServerImpl()
        req = RequestData(
            name="Payment Info",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/payment",
            hidden_response_fields=["tax_id", "billing_account"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                {
                    "tax_id": "99-999",
                    "billing_account": "ACT-123",
                    "name": "Alice",
                }
            )
        )

        out = await impl.call_tool(
            "payment_info",
            {"unmask": True, "reveal": "all"},
        )
        body = _parse_body(out[0])

        self.assertEqual(body["tax_id"], "***")
        self.assertEqual(body["billing_account"], "***")
        self.assertNotIn("99-999", out[0].text)
        self.assertNotIn("ACT-123", out[0].text)

    async def test_mcp_masking_observability_metrics_and_logs(self):
        """Hidden response masking records telemetry metrics and safe structured logs."""
        mock_metrics = MagicMock(spec=MetricsTrackerProtocol)
        impl = MCPServerImpl(metrics=mock_metrics)
        req = RequestData(
            name="Get Customer Secret",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/customers/1",
            hidden_response_fields=["tax_id", "secret_token"],
        )
        impl.register_tools([req])
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(
            body=json.dumps(
                {
                    "tax_id": "99-9999999",
                    "secret_token": "super_secret_val",
                    "username": "alice",
                }
            )
        )

        with self.assertLogs("pypost.core", level=logging.DEBUG) as captured:
            out = await impl.call_tool("get_customer_secret", {})

        body = _parse_body(out[0])
        self.assertEqual(body["tax_id"], "***")
        self.assertEqual(body["secret_token"], "***")
        self.assertEqual(body["username"], "alice")

        mock_metrics.track_hidden_value_mask_applied.assert_called_once_with("mcp")

        all_logs = " ".join(captured.output)
        self.assertIn("mcp_response_masking_applied", all_logs)
        self.assertIn("selector_count=2", all_logs)
        self.assertIn("redact_json_response_fields_completed", all_logs)
        self.assertIn("masked_fields_count=2", all_logs)
        self.assertNotIn("99-9999999", all_logs)
        self.assertNotIn("super_secret_val", all_logs)

    async def test_mcp_masking_observability_malformed_json_fallback_logs(self):
        """Malformed JSON payload logs safe fallback event without leaking raw content."""
        mock_metrics = MagicMock(spec=MetricsTrackerProtocol)
        impl = MCPServerImpl(metrics=mock_metrics)
        req = RequestData(
            name="Broken Payload",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example.com/broken",
            hidden_response_fields=["secret"],
        )
        impl.register_tools([req])
        malformed_raw = "{broken: raw_sensitive_secret_val"
        mock_svc = _stub_request_service(impl)
        mock_svc.execute.return_value = _exec_result(body=malformed_raw)

        with self.assertLogs("pypost.core", level=logging.DEBUG) as captured:
            out = await impl.call_tool("broken_payload", {})

        envelope = _parse_envelope(out[0])
        self.assertEqual(envelope["body"], malformed_raw)

        all_logs = " ".join(captured.output)
        self.assertIn("redact_json_response_fields_skipped_non_json", all_logs)
        self.assertIn("reason=JSONDecodeError", all_logs)
        self.assertNotIn("raw_sensitive_secret_val", all_logs)
