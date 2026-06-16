"""Tests for McpResponseSanitizer (PYPOST-703)."""

import json
import unittest

import pytest

from pypost.core.mcp_response_sanitizer import McpResponseSanitizer
from pypost.core.sensitive_data_masking_policy import HIDDEN_PLACEHOLDER

pytestmark = pytest.mark.timeout(60)


class TestMcpResponseSanitizer(unittest.TestCase):
    def test_redacts_hidden_env_values_in_plain_text(self):
        body = "session=super-secret-token-xyz"
        sanitized = McpResponseSanitizer.sanitize_body(
            body,
            env_vars={"api_key": "super-secret-token-xyz"},
            hidden_keys={"api_key"},
        )
        self.assertEqual(sanitized, f"session={HIDDEN_PLACEHOLDER}")

    def test_redacts_sensitive_json_fields(self):
        body = json.dumps(
            {
                "id": 1,
                "access_token": "abc123",
                "profile": {"api_key": "nested-secret"},
            }
        )
        sanitized = McpResponseSanitizer.sanitize_body(
            body, env_vars={}, hidden_keys=set()
        )
        parsed = json.loads(sanitized)
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["access_token"], HIDDEN_PLACEHOLDER)
        self.assertEqual(parsed["profile"]["api_key"], HIDDEN_PLACEHOLDER)

    def test_redacts_bearer_tokens_in_text(self):
        body = 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig'
        sanitized = McpResponseSanitizer.sanitize_body(
            body, env_vars={}, hidden_keys=set()
        )
        self.assertIn(f"Bearer {HIDDEN_PLACEHOLDER}", sanitized)
        self.assertNotIn("eyJhbGciOi", sanitized)

    def test_redacts_query_tokens_in_urls(self):
        body = "https://api.example.com/data?token=leaked&other=1"
        sanitized = McpResponseSanitizer.sanitize_body(
            body, env_vars={}, hidden_keys=set()
        )
        self.assertIn(f"token={HIDDEN_PLACEHOLDER}", sanitized)
        self.assertNotIn("leaked", sanitized)

    def test_sanitize_logs_applies_same_rules(self):
        logs = ["token=abc123", "ok"]
        sanitized = McpResponseSanitizer.sanitize_logs(
            logs,
            env_vars={"token": "abc123"},
            hidden_keys={"token"},
        )
        self.assertEqual(sanitized[0], f"token={HIDDEN_PLACEHOLDER}")
        self.assertEqual(sanitized[1], "ok")

    def test_non_json_body_left_unchanged_when_no_matches(self):
        body = "plain upstream response"
        sanitized = McpResponseSanitizer.sanitize_body(
            body, env_vars={}, hidden_keys=set()
        )
        self.assertEqual(sanitized, body)
