"""Contract tests for reference collection hidden_response_fields masking (PYPOST-1395).

Validates that:
1. GitHub MCP collection (github_mcp.json) configures hidden_response_fields on
   'github-get-authenticated-user' with bare key and dotted path selectors.
2. GitLab MCP collection (gitlab_mcp.json) configures hidden_response_fields on
   'gitlab-get-current-user' targeting multiple distinct PII email scopes.
3. Jira Cloud MCP collection (jira_mcp.json) configures hidden_response_fields on
   'jira-get-current-user' (bare keys) and 'jira-search-assignable-users' (root array wildcards).
4. Dual presentation and safety surfaces (MCP irreversible '***' sanitization and
   desktop GUI click-to-reveal ResponseView) accurately mask matching fields.
5. All reference collections strictly comply with Collection v2.0.0 schema and
   maintain serialization round-trip fidelity with pristine ResponseData immutability.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from pypost.core.collection_serializer import read_collection_file
from pypost.core.mcp_server_impl import (
    MCPServerImpl,
    format_structured_tool_result,
    normalize_mcp_tool_name,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.request_service import ExecutionResult
from pypost.core.sensitive_text_sanitizer import HIDDEN_PLACEHOLDER
from pypost.models.models import Collection
from pypost.models.response import ResponseData
from pypost.ui.widgets.response_view import ResponseView

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples" / "collections"
GITHUB_COLLECTION_PATH = EXAMPLES_DIR / "github_mcp.json"
GITLAB_COLLECTION_PATH = EXAMPLES_DIR / "gitlab_mcp.json"
JIRA_COLLECTION_PATH = EXAMPLES_DIR / "jira_mcp.json"
GOOGLE_DRIVE_COLLECTION_PATH = EXAMPLES_DIR / "google_drive.json"


def _make_exec_result(
    body: str,
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
            elapsed_time=0.02,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


class TestReferenceCollectionMaskingContract:
    """Automated contract verification for hidden_response_fields across bundled collections."""

    def test_github_mcp_collection_masking_contract(self, qapp: QApplication) -> None:
        """GitHub collection must configure hidden_response_fields on get-authenticated-user."""
        assert GITHUB_COLLECTION_PATH.is_file(), (
            f"GitHub collection fixture not found at {GITHUB_COLLECTION_PATH}"
        )
        collection = read_collection_file(GITHUB_COLLECTION_PATH)
        assert isinstance(collection, Collection)
        assert collection.version in ("1.0.0", "2.0.0")

        req_map = {req.id: req for req in collection.requests}
        assert "github-get-authenticated-user" in req_map, (
            "Reference collection 'github_mcp.json' must contain 'github-get-authenticated-user'"
        )

        user_req = req_map["github-get-authenticated-user"]
        expected_fields = ["email", "two_factor_authentication", "plan.name"]
        assert user_req.hidden_response_fields == expected_fields, (
            f"Request 'github-get-authenticated-user' must configure "
            f"hidden_response_fields={expected_fields}; got {user_req.hidden_response_fields}"
        )

        # Round-trip serialization fidelity
        dumped_json = collection.model_dump_json()
        assert '"hidden_response_fields"' in dumped_json
        for field in expected_fields:
            assert f'"{field}"' in dumped_json

        # Simulation with mock GitHub /user payload
        mock_payload: dict[str, Any] = {
            "login": "octocat",
            "id": 1,
            "email": "octocat@github.com",
            "two_factor_authentication": True,
            "plan": {
                "name": "medium",
                "space": 400,
                "collaborators": 10,
                "private_repos": 20,
            },
            "company": "GitHub",
        }
        raw_body = json.dumps(mock_payload, indent=2)
        exec_res = _make_exec_result(body=raw_body)

        # Verify MCP surface: permanent irreversible redaction
        mcp_out = format_structured_tool_result(
            exec_res,
            hidden_response_fields=user_req.hidden_response_fields,
        )
        mcp_body = json.loads(json.loads(mcp_out)["body"])
        assert mcp_body["email"] == HIDDEN_PLACEHOLDER
        assert mcp_body["two_factor_authentication"] == HIDDEN_PLACEHOLDER
        assert mcp_body["plan"]["name"] == HIDDEN_PLACEHOLDER
        assert mcp_body["plan"]["space"] == 400
        assert mcp_body["login"] == "octocat"
        assert mcp_body["company"] == "GitHub"

        # Verify GUI surface: interactive click-to-reveal tokens
        view = ResponseView()
        try:
            view.display_response(exec_res.response, hidden_fields=user_req.hidden_response_fields)
            view_text = view.body_view.toPlainText()
            assert f'"{HIDDEN_PLACEHOLDER}"' in view_text
            assert "octocat@github.com" not in view_text
            assert "medium" not in view_text
            assert len(view.mask_controller.spans()) == 3
        finally:
            view.close()

        # In-memory ResponseData body immutability
        assert exec_res.response.body == raw_body

    def test_gitlab_mcp_collection_masking_contract(self, qapp: QApplication) -> None:
        """GitLab collection must configure hidden_response_fields on get-current-user."""
        assert GITLAB_COLLECTION_PATH.is_file(), (
            f"GitLab collection fixture not found at {GITLAB_COLLECTION_PATH}"
        )
        collection = read_collection_file(GITLAB_COLLECTION_PATH)
        assert isinstance(collection, Collection)
        assert collection.version in ("1.0.0", "2.0.0")

        req_map = {req.id: req for req in collection.requests}
        assert "gitlab-get-current-user" in req_map, (
            "Reference collection 'gitlab_mcp.json' must contain request 'gitlab-get-current-user'"
        )

        user_req = req_map["gitlab-get-current-user"]
        expected_fields = ["email", "commit_email", "public_email"]
        assert user_req.hidden_response_fields == expected_fields, (
            f"Request 'gitlab-get-current-user' must configure "
            f"hidden_response_fields={expected_fields}; got {user_req.hidden_response_fields}"
        )

        # Round-trip serialization fidelity
        dumped_json = collection.model_dump_json()
        assert '"hidden_response_fields"' in dumped_json
        for field in expected_fields:
            assert f'"{field}"' in dumped_json

        # Simulation with mock GitLab /api/v4/user payload
        mock_payload: dict[str, Any] = {
            "id": 101,
            "username": "john_smith",
            "name": "John Smith",
            "email": "john@example.com",
            "commit_email": "commits@example.com",
            "public_email": "public@example.com",
            "state": "active",
        }
        raw_body = json.dumps(mock_payload, indent=2)
        exec_res = _make_exec_result(body=raw_body)

        # Verify MCP surface
        mcp_out = format_structured_tool_result(
            exec_res,
            hidden_response_fields=user_req.hidden_response_fields,
        )
        mcp_body = json.loads(json.loads(mcp_out)["body"])
        assert mcp_body["email"] == HIDDEN_PLACEHOLDER
        assert mcp_body["commit_email"] == HIDDEN_PLACEHOLDER
        assert mcp_body["public_email"] == HIDDEN_PLACEHOLDER
        assert mcp_body["username"] == "john_smith"
        assert mcp_body["id"] == 101

        # Verify GUI surface
        view = ResponseView()
        try:
            view.display_response(exec_res.response, hidden_fields=user_req.hidden_response_fields)
            view_text = view.body_view.toPlainText()
            assert "john@example.com" not in view_text
            assert "commits@example.com" not in view_text
            assert "public@example.com" not in view_text
            assert len(view.mask_controller.spans()) == 3
        finally:
            view.close()

        # In-memory ResponseData body immutability
        assert exec_res.response.body == raw_body

    def test_jira_mcp_collection_masking_contract(self, qapp: QApplication) -> None:
        """Jira collection must configure hidden_response_fields on user and search endpoints."""
        assert JIRA_COLLECTION_PATH.is_file(), (
            f"Jira collection fixture not found at {JIRA_COLLECTION_PATH}"
        )
        collection = read_collection_file(JIRA_COLLECTION_PATH)
        assert isinstance(collection, Collection)
        assert collection.version == "2.0.0"

        req_map = {req.id: req for req in collection.requests}
        assert "jira-get-current-user" in req_map, (
            "Reference collection 'jira_mcp.json' must contain 'jira-get-current-user'"
        )
        assert "jira-search-assignable-users" in req_map, (
            "Reference collection 'jira_mcp.json' must contain 'jira-search-assignable-users'"
        )

        user_req = req_map["jira-get-current-user"]
        expected_user_fields = ["emailAddress", "accountId"]
        assert user_req.hidden_response_fields == expected_user_fields, (
            f"Request 'jira-get-current-user' must configure "
            f"hidden_response_fields={expected_user_fields}; got {user_req.hidden_response_fields}"
        )

        search_req = req_map["jira-search-assignable-users"]
        expected_search_fields = ["[*].emailAddress", "[*].accountId"]
        assert search_req.hidden_response_fields == expected_search_fields, (
            f"Request 'jira-search-assignable-users' must configure "
            f"hidden_response_fields={expected_search_fields}; "
            f"got {search_req.hidden_response_fields}"
        )

        # Round-trip serialization fidelity
        dumped_json = collection.model_dump_json()
        assert '"hidden_response_fields"' in dumped_json
        for field in expected_user_fields + expected_search_fields:
            assert f'"{field}"' in dumped_json

        # Simulation 1: jira-get-current-user (single object with bare keys)
        mock_user_payload: dict[str, Any] = {
            "accountId": "5b10ac8d82e05b22cc7d4ef5",
            "displayName": "Mia K.",
            "emailAddress": "mia@example.atlassian.net",
            "active": True,
            "timeZone": "UTC",
        }
        user_body = json.dumps(mock_user_payload, indent=2)
        user_res = _make_exec_result(body=user_body)

        mcp_user_out = format_structured_tool_result(
            user_res,
            hidden_response_fields=user_req.hidden_response_fields,
        )
        mcp_user_body = json.loads(json.loads(mcp_user_out)["body"])
        assert mcp_user_body["accountId"] == HIDDEN_PLACEHOLDER
        assert mcp_user_body["emailAddress"] == HIDDEN_PLACEHOLDER
        assert mcp_user_body["displayName"] == "Mia K."

        view1 = ResponseView()
        try:
            view1.display_response(user_res.response, hidden_fields=user_req.hidden_response_fields)
            view_text1 = view1.body_view.toPlainText()
            assert "mia@example.atlassian.net" not in view_text1
            assert "5b10ac8d82e05b22cc7d4ef5" not in view_text1
            assert len(view1.mask_controller.spans()) == 2
        finally:
            view1.close()

        # Simulation 2: jira-search-assignable-users (root array with wildcard selectors)
        mock_search_payload: list[dict[str, Any]] = [
            {
                "accountId": "user-1",
                "displayName": "User One",
                "emailAddress": "user1@example.com",
            },
            {
                "accountId": "user-2",
                "displayName": "User Two",
                "emailAddress": "user2@example.com",
            },
        ]
        search_body = json.dumps(mock_search_payload, indent=2)
        search_res = _make_exec_result(body=search_body)

        mcp_search_out = format_structured_tool_result(
            search_res,
            hidden_response_fields=search_req.hidden_response_fields,
        )
        mcp_search_body = json.loads(json.loads(mcp_search_out)["body"])
        assert mcp_search_body[0]["accountId"] == HIDDEN_PLACEHOLDER
        assert mcp_search_body[0]["emailAddress"] == HIDDEN_PLACEHOLDER
        assert mcp_search_body[0]["displayName"] == "User One"
        assert mcp_search_body[1]["accountId"] == HIDDEN_PLACEHOLDER
        assert mcp_search_body[1]["emailAddress"] == HIDDEN_PLACEHOLDER
        assert mcp_search_body[1]["displayName"] == "User Two"

        view2 = ResponseView()
        try:
            view2.display_response(
                search_res.response,
                hidden_fields=search_req.hidden_response_fields,
            )
            view_text2 = view2.body_view.toPlainText()
            assert "user1@example.com" not in view_text2
            assert "user2@example.com" not in view_text2
            assert len(view2.mask_controller.spans()) == 4
        finally:
            view2.close()

        assert user_res.response.body == user_body
        assert search_res.response.body == search_body

    def test_all_reference_collections_schema_and_version_invariants(self) -> None:
        """All bundled collections conform to Collection schema and have hidden_response_fields."""
        reference_targets: list[tuple[Path, dict[str, list[str]]]] = [
            (
                GOOGLE_DRIVE_COLLECTION_PATH,
                {
                    "gdrive-about-get": [
                        "emailAddress",
                        "permissionId",
                        "user.emailAddress",
                    ],
                },
            ),
            (
                GITHUB_COLLECTION_PATH,
                {
                    "github-get-authenticated-user": [
                        "email",
                        "two_factor_authentication",
                        "plan.name",
                    ],
                },
            ),
            (
                GITLAB_COLLECTION_PATH,
                {
                    "gitlab-get-current-user": [
                        "email",
                        "commit_email",
                        "public_email",
                    ],
                },
            ),
            (
                JIRA_COLLECTION_PATH,
                {
                    "jira-get-current-user": [
                        "emailAddress",
                        "accountId",
                    ],
                    "jira-search-assignable-users": [
                        "[*].emailAddress",
                        "[*].accountId",
                    ],
                },
            ),
        ]

        for path, expected_req_masks in reference_targets:
            assert path.is_file(), f"Reference collection file missing: {path}"
            collection = read_collection_file(path)
            assert isinstance(collection, Collection)
            assert collection.version in ("1.0.0", "2.0.0")

            # Check that every single request has hidden_response_fields attribute as a list
            for req in collection.requests:
                assert isinstance(req.hidden_response_fields, list), (
                    f"Request {req.id} in {path.name} must have list hidden_response_fields"
                )

            # Check target request masking expectations
            req_map = {req.id: req for req in collection.requests}
            for req_id, expected_fields in expected_req_masks.items():
                assert req_id in req_map, (
                    f"Expected request '{req_id}' in {path.name}"
                )
                actual_fields = req_map[req_id].hidden_response_fields
                assert actual_fields == expected_fields, (
                    f"Collection {path.name} request '{req_id}' expected hidden_response_fields "
                    f"{expected_fields}, got {actual_fields}"
                )

    def test_reference_collections_observability_and_zero_leakage_contract(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify metrics and structured logging emit without sensitive data leakage."""
        # 1. Collection file loading emits structured logs without leaking payload content
        with caplog.at_level(logging.DEBUG, logger="pypost.core.collection_serializer"):
            github_col = read_collection_file(GITHUB_COLLECTION_PATH)
            gitlab_col = read_collection_file(GITLAB_COLLECTION_PATH)
            jira_col = read_collection_file(JIRA_COLLECTION_PATH)

        load_records = [
            r for r in caplog.records if r.name == "pypost.core.collection_serializer"
        ]
        assert len(github_col.requests) > 0
        assert len(gitlab_col.requests) > 0
        assert len(jira_col.requests) > 0
        assert any(
            "collection_file_read" in r.message and "github_mcp.json" in r.message
            for r in load_records
        )
        assert any(
            "collection_file_read" in r.message and "gitlab_mcp.json" in r.message
            for r in load_records
        )
        assert any(
            "collection_file_read" in r.message and "jira_mcp.json" in r.message
            for r in load_records
        )

        # 2. Verify Desktop GUI presentation observability & zero leakage
        mock_gui_metrics = MagicMock(spec=MetricsTrackerProtocol)
        view = ResponseView(metrics=mock_gui_metrics)
        try:
            # GitHub request with sensitive values
            github_req = {r.id: r for r in github_col.requests}["github-get-authenticated-user"]
            github_secret = "secret-octo-token-val"
            github_email = "octocat@github.internal"
            github_payload = json.dumps(
                {
                    "login": "octocat",
                    "email": github_email,
                    "two_factor_authentication": True,
                    "plan": {"name": "enterprise-secret-tier", "space": 9999},
                    "custom_secret": github_secret,
                }
            )
            github_resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=github_payload,
                elapsed_time=0.03,
                size=len(github_payload),
            )
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                view.display_response(
                    github_resp, hidden_fields=github_req.hidden_response_fields
                )

            mock_gui_metrics.track_hidden_value_mask_applied.assert_called_with("gui_response")
            assert any(
                "response_masking_initialized span_count=3 selectors_count=3" in r.message
                for r in caplog.records
            )
            assert not any(github_email in r.message for r in caplog.records)
            assert not any("enterprise-secret-tier" in r.message for r in caplog.records)

            # Click-to-reveal toggle logging does not leak secret values
            spans = view.mask_controller.spans()
            assert len(spans) == 3
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                view.mask_controller.handle_click(spans[0].start_pos + 1)
            assert any(
                "click_to_reveal_toggle" in r.message and "revealed=True" in r.message
                for r in caplog.records
            )
            assert not any(github_email in r.message for r in caplog.records)
        finally:
            view.close()

        # 3. Verify MCP tool execution observability & zero leakage
        mock_mcp_metrics = MagicMock(spec=MetricsTrackerProtocol)
        mcp_server = MCPServerImpl(metrics=mock_mcp_metrics)
        jira_req = {r.id: r for r in jira_col.requests}["jira-get-current-user"]
        mcp_server.register_tools([jira_req])
        tool_name = normalize_mcp_tool_name(jira_req.name)

        jira_account_id = "jira-user-secret-account-id-12345"
        jira_email = "jira-user@private-domain.org"
        jira_payload = json.dumps(
            {
                "accountId": jira_account_id,
                "displayName": "Jira Admin",
                "emailAddress": jira_email,
                "active": True,
            }
        )
        mock_svc = MagicMock()
        mock_svc.execute.return_value = _make_exec_result(body=jira_payload)
        mcp_server._create_request_service = lambda: mock_svc

        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            tool_res = asyncio.run(mcp_server.call_tool(tool_name, {}))

        mock_mcp_metrics.track_hidden_value_mask_applied.assert_called_with("mcp")
        assert any("mcp_response_masking_applied" in r.message for r in caplog.records)
        assert any("redact_json_response_fields_completed" in r.message for r in caplog.records)
        assert not any(jira_account_id in r.message for r in caplog.records)
        assert not any(jira_email in r.message for r in caplog.records)

        # Assert MCP egress tool result text is sanitized
        tool_result_text = tool_res[0].text
        assert jira_account_id not in tool_result_text
        assert jira_email not in tool_result_text
        assert HIDDEN_PLACEHOLDER in tool_result_text
