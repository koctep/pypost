"""Integration test suite and edge-case verification for hidden response fields (PYPOST-1380).

Verifies cross-cutting E2E contracts, AST selector edge cases, multi-tab isolation,
and reference collection fixture integration for response field masking:
- Scenario 1: Cross-cutting E2E contract (MCP permanent masking + GUI click-to-reveal).
- Scenario 2: Deeply nested paths (>5 levels).
- Scenario 3: Array wildcard selectors (items[*].token, root arrays [*].id, heterogeneous).
- Scenario 4: Non-string primitive values (integers, floats, booleans, nulls).
- Scenario 5: Duplicate key names across distinct branch paths disambiguated by dot notation.
- Scenario 6: Non-JSON payloads (HTML error page, plain text, malformed JSON) and empty (204).
- Scenario 7: Multi-tab concurrency isolation and independent draft state.
- Scenario 8: Reference collection fixture validation (google_drive.json gdrive-about-get).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from pypost.core.collection_serializer import read_collection_file
from pypost.core.mcp_server_impl import (
    MCPServerImpl,
    format_structured_tool_result,
)
from pypost.core.request_persisted_fields import (
    copy_request_for_isolated_tab,
    persisted_fields_equal,
    request_draft_fields_equal,
    snapshot_persisted_fields,
)
from pypost.core.request_service import ExecutionResult
from pypost.core.sensitive_text_sanitizer import (
    HIDDEN_PLACEHOLDER,
    redact_json_response_fields,
)
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.ui.widgets.response_view import ResponseView

pytestmark = pytest.mark.timeout(60)

REPO_ROOT = Path(__file__).resolve().parents[1]
GOOGLE_DRIVE_COLLECTION_PATH = REPO_ROOT / "examples" / "collections" / "google_drive.json"


def _make_exec_result(
    body: str = "",
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> ExecutionResult:
    """Create a mock ExecutionResult with authentic ResponseData."""
    resp_headers = {"Content-Type": "application/json"}
    if headers:
        resp_headers.update(headers)
    return ExecutionResult(
        response=ResponseData(
            status_code=status_code,
            headers=resp_headers,
            body=body,
            elapsed_time=0.05,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


class TestHiddenResponseFieldsIntegrationEdgeCases:
    """End-to-end integration and edge-case test suite for response field masking."""

    def test_scenario_1_cross_cutting_e2e_contract(self, qapp: QApplication) -> None:
        """Scenario 1: Cross-cutting E2E contract on the exact same execution response.

        Tests MCP permanent masking (irreversible) and GUI click-to-reveal on the same
        ResponseData instance while asserting the underlying response.body remains unmutated.
        """
        raw_body_dict: dict[str, Any] = {
            "token": "secret_token_123",
            "client_secret": "my_client_secret_xyz",
            "user": {
                "id": 9999,
                "username": "alice",
            },
            "status": "active",
        }
        original_body_str = json.dumps(raw_body_dict, indent=2)
        exec_result = _make_exec_result(body=original_body_str)
        req = RequestData(
            name="Get Account Profile",
            expose_as_mcp=True,
            method="GET",
            url="https://api.example.com/account",
            hidden_response_fields=["token", "client_secret", "user.id"],
        )

        # --- Surface 1: Permanent MCP Output Boundary ---
        mcp_output_str = format_structured_tool_result(
            exec_result,
            hidden_response_fields=req.hidden_response_fields,
        )
        envelope = json.loads(mcp_output_str)
        assert envelope["status"] == 200
        assert envelope["error"] is False
        mcp_body = json.loads(envelope["body"])
        assert mcp_body["token"] == HIDDEN_PLACEHOLDER
        assert mcp_body["client_secret"] == HIDDEN_PLACEHOLDER
        assert mcp_body["user"]["id"] == HIDDEN_PLACEHOLDER
        assert mcp_body["user"]["username"] == "alice"
        assert mcp_body["status"] == "active"

        # Verify MCP tool schema exposes zero reveal/unmask parameters
        server = MCPServerImpl()
        server.register_tools([req])
        tools = asyncio.run(server.list_tools())
        assert len(tools) == 1
        input_props = tools[0].inputSchema.get("properties", {})
        assert not any("reveal" in p.lower() or "unmask" in p.lower() for p in input_props)

        # --- Surface 2: Interactive Desktop GUI ResponseView ---
        view = ResponseView()
        try:
            view.display_response(exec_result.response, hidden_fields=req.hidden_response_fields)
            displayed_text = view.body_view.toPlainText()
            assert f'"token": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert f'"client_secret": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert f'"id": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert '"username": "alice"' in displayed_text
            assert '"status": "active"' in displayed_text

            spans = view.mask_controller.spans()
            assert len(spans) == 3
            assert all(not span.is_revealed for span in spans)

            # In-place click-to-reveal token
            token_span = next(s for s in spans if s.path == "token")
            toggled = view.mask_controller.handle_click(token_span.start_pos + 1)
            assert toggled is True
            assert "secret_token_123" in view.body_view.toPlainText()
            assert token_span.is_revealed is True

            # In-place click-to-remask token
            toggled_again = view.mask_controller.handle_click(token_span.start_pos + 1)
            assert toggled_again is True
            assert "secret_token_123" not in view.body_view.toPlainText()
            assert f'"{HIDDEN_PLACEHOLDER}"' in view.body_view.toPlainText()
            assert token_span.is_revealed is False
        finally:
            view.close()

        # Invariant: Raw in-memory ResponseData is completely unmutated across both surfaces
        assert exec_result.response.body == original_body_str

    def test_scenario_2_deeply_nested_paths(self, qapp: QApplication) -> None:
        """Scenario 2: Deeply nested paths (>5 levels, e.g. a.b.c.d.e.f.secret).

        Verifies that fully qualified dot-notation correctly resolves deep hierarchies
        without affecting siblings or parallel branches at the same depth.
        """
        payload: dict[str, Any] = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "level6": {
                                    "secret": "deep_vault_pass_999",
                                    "public": "safe_depth_6",
                                }
                            }
                        },
                        "other": {
                            "secret": "parallel_branch_secret",
                        },
                    }
                }
            }
        }
        raw_json = json.dumps(payload, indent=2)
        selector = "level1.level2.level3.level4.level5.level6.secret"

        # MCP Redaction
        redacted_raw = redact_json_response_fields(raw_json, [selector])
        redacted = json.loads(redacted_raw)
        assert (
            redacted["level1"]["level2"]["level3"]["level4"]["level5"]["level6"]["secret"]
            == HIDDEN_PLACEHOLDER
        )
        assert (
            redacted["level1"]["level2"]["level3"]["level4"]["level5"]["level6"]["public"]
            == "safe_depth_6"
        )
        assert (
            redacted["level1"]["level2"]["level3"]["other"]["secret"]
            == "parallel_branch_secret"
        )

        # GUI ResponseView
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=raw_json,
                elapsed_time=0.01,
                size=len(raw_json.encode("utf-8")),
            )
            view.display_response(resp, hidden_fields=[selector])
            text = view.body_view.toPlainText()
            assert f'"secret": "{HIDDEN_PLACEHOLDER}"' in text
            assert '"public": "safe_depth_6"' in text
            assert '"secret": "parallel_branch_secret"' in text

            spans = view.mask_controller.spans()
            assert len(spans) == 1
            assert spans[0].path == selector

            # Reveal and re-mask toggle
            assert view.mask_controller.handle_click(spans[0].start_pos + 1) is True
            assert "deep_vault_pass_999" in view.body_view.toPlainText()
            assert view.mask_controller.handle_click(spans[0].start_pos + 1) is True
            assert "deep_vault_pass_999" not in view.body_view.toPlainText()
        finally:
            view.close()

    def test_scenario_3_array_wildcard_selectors(self, qapp: QApplication) -> None:
        """Scenario 3: Array wildcard selectors (items[*].token, root arrays [*].id, heterogeneous).

        Asserts that list indexing and wildcard expressions mask repeating elements.
        """
        # Part A: Nested array wildcard `items[*].token`
        nested_payload = {
            "items": [
                {"id": 1, "token": "alpha_token", "name": "Item A"},
                {"id": 2, "token": "beta_token", "name": "Item B"},
                {"id": 3, "other": "no_token", "name": "Item C"},
            ],
            "meta": {"page": 1},
        }
        nested_json = json.dumps(nested_payload, indent=2)
        redacted_nested = json.loads(
            redact_json_response_fields(nested_json, ["items[*].token"])
        )
        assert redacted_nested["items"][0]["token"] == HIDDEN_PLACEHOLDER
        assert redacted_nested["items"][1]["token"] == HIDDEN_PLACEHOLDER
        assert redacted_nested["items"][0]["name"] == "Item A"
        assert redacted_nested["items"][1]["name"] == "Item B"
        assert redacted_nested["items"][2]["other"] == "no_token"
        assert redacted_nested["meta"]["page"] == 1

        # Part B: Root array wildcard `[*].id`
        root_payload = [
            {"id": "root_sec_1", "title": "First"},
            {"id": "root_sec_2", "title": "Second"},
        ]
        root_json = json.dumps(root_payload, indent=2)
        redacted_root = json.loads(
            redact_json_response_fields(root_json, ["[*].id"])
        )
        assert redacted_root[0]["id"] == HIDDEN_PLACEHOLDER
        assert redacted_root[1]["id"] == HIDDEN_PLACEHOLDER
        assert redacted_root[0]["title"] == "First"
        assert redacted_root[1]["title"] == "Second"

        # Part C: Heterogeneous arrays
        hetero_payload = {
            "items": [
                {"token": "hetero_secret"},
                "primitive_string",
                123,
                None,
                [],
                {},
                {"other": "clean"},
            ]
        }
        hetero_json = json.dumps(hetero_payload, indent=2)
        redacted_hetero = json.loads(
            redact_json_response_fields(hetero_json, ["items[*].token"])
        )
        assert redacted_hetero["items"][0]["token"] == HIDDEN_PLACEHOLDER
        assert redacted_hetero["items"][1] == "primitive_string"
        assert redacted_hetero["items"][2] == 123
        assert redacted_hetero["items"][3] is None

        # GUI ResponseView verification for array wildcards
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=nested_json,
                elapsed_time=0.01,
                size=len(nested_json.encode("utf-8")),
            )
            view.display_response(resp, hidden_fields=["items[*].token"])
            spans = view.mask_controller.spans()
            assert len(spans) == 2

            # Reveal both spans
            assert view.mask_controller.handle_click(spans[0].start_pos + 1) is True
            assert "alpha_token" in view.body_view.toPlainText()
            assert view.mask_controller.handle_click(spans[1].start_pos + 1) is True
            assert "beta_token" in view.body_view.toPlainText()
        finally:
            view.close()

    def test_scenario_4_non_string_primitives_and_null_masking(self, qapp: QApplication) -> None:
        """Scenario 4: Non-string primitive values (integers, floats, booleans, nulls).

        Asserts that non-string primitives are masked cleanly as '***' in MCP and GUI,
        and click-to-reveal displays the literal representation (42, 3.1415, true, false, null).
        """
        payload: dict[str, Any] = {
            "pin": 1234,
            "ratio": 3.1415,
            "active": True,
            "disabled": False,
            "empty": None,
            "unmasked_str": "hello",
        }
        raw_json = json.dumps(payload, indent=2)
        hidden_fields = ["pin", "ratio", "active", "disabled", "empty"]

        # MCP Redaction
        redacted = json.loads(redact_json_response_fields(raw_json, hidden_fields))
        assert redacted["pin"] == HIDDEN_PLACEHOLDER
        assert redacted["ratio"] == HIDDEN_PLACEHOLDER
        assert redacted["active"] == HIDDEN_PLACEHOLDER
        assert redacted["disabled"] == HIDDEN_PLACEHOLDER
        assert redacted["empty"] == HIDDEN_PLACEHOLDER
        assert redacted["unmasked_str"] == "hello"

        # GUI ResponseView
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=raw_json,
                elapsed_time=0.01,
                size=len(raw_json.encode("utf-8")),
            )
            view.display_response(resp, hidden_fields=hidden_fields)
            displayed_text = view.body_view.toPlainText()
            assert f'"pin": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert f'"ratio": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert f'"active": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert f'"disabled": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert f'"empty": "{HIDDEN_PLACEHOLDER}"' in displayed_text
            assert '"unmasked_str": "hello"' in displayed_text

            spans = view.mask_controller.spans()
            assert len(spans) == 5

            span_map = {s.path: s for s in spans}
            # Verify reveal and raw values
            assert span_map["pin"].raw_value == "1234"
            assert span_map["ratio"].raw_value == "3.1415"
            assert span_map["active"].raw_value == "true"
            assert span_map["disabled"].raw_value == "false"
            assert span_map["empty"].raw_value == "null"

            # Click to reveal pin
            pin_span = span_map["pin"]
            assert view.mask_controller.handle_click(pin_span.start_pos + 1) is True
            assert "1234" in view.body_view.toPlainText()
            # Click to re-mask pin
            assert view.mask_controller.handle_click(pin_span.start_pos + 1) is True
            assert "1234" not in view.body_view.toPlainText()
        finally:
            view.close()

    def test_scenario_5_duplicate_keys_in_distinct_branches(self, qapp: QApplication) -> None:
        """Scenario 5: Duplicate keys across branches disambiguated by dot-notation.

        Asserts that 'user.id' masks only user.id, while 'name' masks all occurrences.
        """
        payload: dict[str, Any] = {
            "user": {"id": 101, "name": "alice"},
            "organization": {"id": 202, "name": "acme"},
            "metadata": {"id": 303, "version": 1},
        }
        raw_json = json.dumps(payload, indent=2)

        # 5.1 Qualified selector 'user.id'
        redacted_user_id = json.loads(redact_json_response_fields(raw_json, ["user.id"]))
        assert redacted_user_id["user"]["id"] == HIDDEN_PLACEHOLDER
        assert redacted_user_id["organization"]["id"] == 202
        assert redacted_user_id["metadata"]["id"] == 303

        view1 = ResponseView()
        try:
            resp1 = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=raw_json,
                elapsed_time=0.01,
                size=len(raw_json.encode("utf-8")),
            )
            view1.display_response(resp1, hidden_fields=["user.id"])
            spans = view1.mask_controller.spans()
            assert len(spans) == 1
            assert spans[0].path == "user.id"
        finally:
            view1.close()

        # 5.2 Unqualified root selector 'name'
        redacted_name = json.loads(redact_json_response_fields(raw_json, ["name"]))
        assert redacted_name["user"]["name"] == HIDDEN_PLACEHOLDER
        assert redacted_name["organization"]["name"] == HIDDEN_PLACEHOLDER
        assert redacted_name["user"]["id"] == 101
        assert redacted_name["organization"]["id"] == 202

        view2 = ResponseView()
        try:
            resp2 = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=raw_json,
                elapsed_time=0.01,
                size=len(raw_json.encode("utf-8")),
            )
            view2.display_response(resp2, hidden_fields=["name"])
            spans2 = view2.mask_controller.spans()
            assert len(spans2) == 2
            paths = {s.path for s in spans2}
            assert paths == {"user.name", "organization.name"}
        finally:
            view2.close()

    def test_scenario_6_non_json_and_empty_response_handling(self, qapp: QApplication) -> None:
        """Scenario 6: Non-JSON payloads (HTML error page, plain text, malformed) and empty (204).

        Asserts that non-JSON content is safely passed through without crashes or exceptions.
        """
        hidden = ["token", "secret"]

        # Case 1: HTML 500 error page
        html_body = "<html><body><h1>500 Internal Server Error</h1></body></html>"
        res_html = _make_exec_result(
            body=html_body, status_code=500, headers={"Content-Type": "text/html"}
        )
        mcp_html = json.loads(
            format_structured_tool_result(res_html, hidden_response_fields=hidden)
        )
        assert mcp_html["body"] == html_body

        view = ResponseView()
        try:
            view.display_response(res_html.response, hidden_fields=hidden)
            assert view.body_view.toPlainText() == html_body
            assert len(view.mask_controller.spans()) == 0

            # Case 2: Plain text
            text_body = "Authentication failed: invalid token provided"
            res_text = _make_exec_result(
                body=text_body, status_code=401, headers={"Content-Type": "text/plain"}
            )
            mcp_text = json.loads(
                format_structured_tool_result(res_text, hidden_response_fields=hidden)
            )
            assert mcp_text["body"] == text_body
            view.display_response(res_text.response, hidden_fields=hidden)
            assert view.body_view.toPlainText() == text_body
            assert len(view.mask_controller.spans()) == 0

            # Case 3: Malformed JSON
            broken_json = '{"error": "broken", "list": [1, 2, '
            res_broken = _make_exec_result(body=broken_json, status_code=200)
            mcp_broken = json.loads(
                format_structured_tool_result(res_broken, hidden_response_fields=hidden)
            )
            assert mcp_broken["body"] == broken_json
            view.display_response(res_broken.response, hidden_fields=hidden)
            assert view.body_view.toPlainText() == broken_json
            assert len(view.mask_controller.spans()) == 0

            # Case 4: Empty response (HTTP 204 No Content)
            res_empty = _make_exec_result(body="", status_code=204, headers={})
            mcp_empty = json.loads(
                format_structured_tool_result(res_empty, hidden_response_fields=hidden)
            )
            assert mcp_empty["body"] == ""
            view.display_response(res_empty.response, hidden_fields=hidden)
            assert view.body_view.toPlainText() == ""
            assert view.status_label.text() == "Status: 204"
            assert len(view.mask_controller.spans()) == 0
        finally:
            view.close()

    def test_scenario_7_multi_tab_concurrency_isolation(self, qapp: QApplication) -> None:
        """Scenario 7: Multi-tab concurrency isolation and draft independence.

        Asserts that copying requests across tabs creates deep isolated copies of
        hidden_response_fields, ensuring draft mutations in Tab B do not bleed into Tab A.
        """
        req_a = RequestData(
            id="req-tab-a",
            name="Tab A Request",
            hidden_response_fields=["token"],
        )
        req_b = copy_request_for_isolated_tab(req_a)
        req_b.id = "req-tab-b"
        req_b.name = "Tab B Request"
        req_b.hidden_response_fields.append("user.secret")

        # Tab isolation assertion
        assert req_a.hidden_response_fields == ["token"]
        assert req_b.hidden_response_fields == ["token", "user.secret"]
        assert not persisted_fields_equal(req_a, req_b)
        assert not request_draft_fields_equal(req_a, req_b)

        # Baseline snapshot isolation
        baseline_a = snapshot_persisted_fields(req_a)
        baseline_b = snapshot_persisted_fields(req_b)
        assert persisted_fields_equal(baseline_a, req_a)
        assert persisted_fields_equal(baseline_b, req_b)
        assert not persisted_fields_equal(baseline_a, baseline_b)

        # Concurrent ResponseView display
        shared_payload = json.dumps(
            {"token": "tok_val", "user": {"secret": "sec_val"}, "status": "ok"},
            indent=2,
        )
        resp = ResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=shared_payload,
            elapsed_time=0.01,
            size=len(shared_payload.encode("utf-8")),
        )
        view_a = ResponseView()
        view_b = ResponseView()
        try:
            view_a.display_response(resp, hidden_fields=req_a.hidden_response_fields)
            view_b.display_response(resp, hidden_fields=req_b.hidden_response_fields)

            assert len(view_a.mask_controller.spans()) == 1
            assert len(view_b.mask_controller.spans()) == 2
            assert '"secret": "sec_val"' in view_a.body_view.toPlainText()
            assert f'"secret": "{HIDDEN_PLACEHOLDER}"' in view_b.body_view.toPlainText()

            # Mutate span state in view_a and verify view_b span state is completely unaffected
            span_a = view_a.mask_controller.spans()[0]
            view_a.mask_controller.handle_click(span_a.start_pos + 1)
            assert span_a.is_revealed is True
            assert view_b.mask_controller.spans()[0].is_revealed is False
        finally:
            view_a.close()
            view_b.close()

    def test_scenario_8_reference_collection_fixture_validation(self, qapp: QApplication) -> None:
        """Scenario 8: Reference collection fixture validation.

        Asserts that examples/collections/google_drive.json contains a dedicated
        request ('gdrive-about-get') configured with hidden_response_fields:
        ["emailAddress", "permissionId", "user.emailAddress"].

        This test serves as the automated failing repro for Step 3 and will fail
        in the red state until Step 4 updates the collection fixture.
        """
        assert GOOGLE_DRIVE_COLLECTION_PATH.is_file(), (
            f"Google Drive collection fixture not found at {GOOGLE_DRIVE_COLLECTION_PATH}"
        )
        collection = read_collection_file(GOOGLE_DRIVE_COLLECTION_PATH)
        req_map = {req.id: req for req in collection.requests}

        # Failing repro assertion: gdrive-about-get must exist in the reference collection
        assert "gdrive-about-get" in req_map, (
            "Reference collection 'google_drive.json' must contain sample request "
            "'gdrive-about-get' demonstrating hidden_response_fields configuration"
        )
        about_req = req_map["gdrive-about-get"]
        assert about_req.hidden_response_fields == [
            "emailAddress",
            "permissionId",
            "user.emailAddress",
        ], (
            f"Request 'gdrive-about-get' must configure hidden_response_fields; "
            f"got {about_req.hidden_response_fields}"
        )

        # Round-trip serialization must preserve hidden_response_fields
        dumped_json = collection.model_dump_json()
        assert '"hidden_response_fields"' in dumped_json
        assert '"emailAddress"' in dumped_json
        assert '"permissionId"' in dumped_json
        assert '"user.emailAddress"' in dumped_json

        # Executing mock Google Drive /about response through MCP and GUI masking pipelines
        mock_about_payload = {
            "user": {
                "displayName": "Alex Developer",
                "emailAddress": "alex@example.com",
                "permissionId": "perm_987654",
            },
            "storageQuota": {
                "limit": "107374182400",
                "usage": "10737418240",
            },
        }
        mock_raw = json.dumps(mock_about_payload, indent=2)
        exec_res = _make_exec_result(body=mock_raw)

        # MCP check
        mcp_out = format_structured_tool_result(
            exec_res,
            hidden_response_fields=about_req.hidden_response_fields,
        )
        mcp_body = json.loads(json.loads(mcp_out)["body"])
        assert mcp_body["user"]["emailAddress"] == HIDDEN_PLACEHOLDER
        assert mcp_body["user"]["permissionId"] == HIDDEN_PLACEHOLDER
        assert mcp_body["user"]["displayName"] == "Alex Developer"
        assert mcp_body["storageQuota"]["limit"] == "107374182400"

        # GUI check
        view = ResponseView()
        try:
            view.display_response(exec_res.response, hidden_fields=about_req.hidden_response_fields)
            view_text = view.body_view.toPlainText()
            assert f'"emailAddress": "{HIDDEN_PLACEHOLDER}"' in view_text
            assert f'"permissionId": "{HIDDEN_PLACEHOLDER}"' in view_text
            assert '"displayName": "Alex Developer"' in view_text
            assert len(view.mask_controller.spans()) == 2
        finally:
            view.close()
