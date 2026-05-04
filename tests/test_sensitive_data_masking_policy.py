import unittest

from pypost.core.sensitive_data_masking_policy import SensitiveDataMaskingPolicy
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData


class TestSensitiveDataMaskingPolicyBuildHistorySafeFields(unittest.TestCase):

    def setUp(self):
        self.ts = TemplateService()
        self.policy = SensitiveDataMaskingPolicy(self.ts)

    def test_masks_hidden_variable_in_url_query_param(self):
        req = RequestData(method="GET", url="http://example.com?token={{token}}")
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"token": "supersecret"},
            hidden_keys={"token"},
        )
        self.assertEqual("http://example.com?token=***", result.url)

    def test_masks_hidden_variable_in_header_value(self):
        req = RequestData(
            method="GET",
            url="http://x",
            headers={"Authorization": "Bearer {{token}}"},
        )
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"token": "supersecret"},
            hidden_keys={"token"},
        )
        self.assertEqual("Bearer ***", result.headers["Authorization"])

    def test_masks_hidden_variable_in_body(self):
        req = RequestData(
            method="POST",
            url="http://x",
            body='{"token":"{{token}}","user":"{{user}}"}',
        )
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"token": "supersecret", "user": "alice"},
            hidden_keys={"token"},
        )
        self.assertEqual('{"token":"***","user":"alice"}', result.body)

    def test_non_hidden_variables_remain_unmasked(self):
        req = RequestData(method="GET", url="http://{{host}}/api?token={{token}}")
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"host": "myserver.com", "token": "supersecret"},
            hidden_keys={"token"},
        )
        self.assertIn("myserver.com", result.url)
        self.assertNotIn("supersecret", result.url)
        self.assertIn("***", result.url)

    def test_empty_hidden_keys_renders_but_does_not_mask(self):
        req = RequestData(method="GET", url="http://{{host}}?token={{token}}")
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"host": "myserver.com", "token": "supersecret"},
            hidden_keys=set(),
        )
        self.assertIn("supersecret", result.url)
        self.assertIn("myserver.com", result.url)

    def test_none_hidden_keys_renders_but_does_not_mask(self):
        req = RequestData(method="GET", url="http://{{host}}?token={{token}}")
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"host": "myserver.com", "token": "supersecret"},
            hidden_keys=None,
        )
        self.assertIn("supersecret", result.url)
        self.assertIn("myserver.com", result.url)

    def test_hidden_key_not_in_variables_is_silently_skipped(self):
        req = RequestData(method="GET", url="http://example.com")
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"host": "myserver.com"},
            hidden_keys={"token"},
        )
        self.assertEqual("http://example.com", result.url)

    def test_multiple_hidden_keys_all_masked(self):
        req = RequestData(
            method="POST",
            url="http://{{host}}/api",
            headers={"X-Api-Key": "{{api_key}}"},
            body="token={{token}}&key={{api_key}}",
        )
        result = self.policy.build_history_safe_fields(
            request=req,
            variables={"host": "myserver.com", "token": "tok123", "api_key": "key456"},
            hidden_keys={"token", "api_key"},
        )
        self.assertNotIn("tok123", result.url + result.headers.get("X-Api-Key", "") + result.body)
        self.assertNotIn("key456", result.url + result.headers.get("X-Api-Key", "") + result.body)
        self.assertEqual("***", result.headers["X-Api-Key"])


if __name__ == "__main__":
    unittest.main()
