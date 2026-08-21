import os
import unittest
from unittest.mock import patch
import pytest

from pypost.core.environment_variable_resolver import (
    EnvironmentVariableResolver,
    resolve_environment_variables,
)
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData
from pypost.core.http_client import HTTPClient
from pypost.core.curl_generator import CurlGenerator
from pypost.ui.widgets.mixins import VariableHoverResolver

pytestmark = pytest.mark.timeout(30)


class TestEnvironmentVariableResolver(unittest.TestCase):
    def setUp(self):
        self.template_service = TemplateService()
        self.resolver = EnvironmentVariableResolver(self.template_service)
        self._orig_hover_service = VariableHoverResolver._template_service()
        VariableHoverResolver.set_template_service(self.template_service)

    def tearDown(self):
        VariableHoverResolver.set_template_service(self._orig_hover_service)

    def test_static_variables_pass_through_unchanged(self):
        variables = {
            "host": "localhost",
            "port": "8080",
            "prefix": "api",
        }
        resolved = self.resolver.resolve(variables)
        self.assertEqual(variables, resolved)

    def test_cross_variable_reference_resolution(self):
        variables = {
            "host": "localhost",
            "port": "8080",
            "base_url": "http://{{host}}:{{port}}",
            "api_endpoint": "{{base_url}}/v1/users",
        }
        resolved = self.resolver.resolve(variables)
        self.assertEqual("http://localhost:8080", resolved["base_url"])
        self.assertEqual("http://localhost:8080/v1/users", resolved["api_endpoint"])
        self.assertEqual("localhost", resolved["host"])
        self.assertEqual("8080", resolved["port"])

    def test_builtin_function_expressions_in_variables(self):
        with patch.dict(os.environ, {"SECRET_KEY": "my-api-token-999"}):
            variables = {
                "raw_token": "{{env(SECRET_KEY)}}",
                "auth_header": "Bearer {{base64(raw_token)}}",
                "hashed_token": "{{md5(raw_token)}}",
                "query_param": "{{urlencode(raw_token)}}",
            }
            resolved = self.resolver.resolve(variables)
            self.assertEqual("my-api-token-999", resolved["raw_token"])
            self.assertEqual("Bearer bXktYXBpLXRva2VuLTk5OQ==", resolved["auth_header"])
            self.assertEqual("63abbea240e2eeb1c29aa3167a3fe5e6", resolved["hashed_token"])
            self.assertEqual("my-api-token-999", resolved["query_param"])

    def test_direct_os_env_identifier_without_pypost_variable(self):
        with patch.dict(os.environ, {"SYSTEM_HOST": "api.prod.company.com"}):
            variables = {
                "host": "{{env(SYSTEM_HOST)}}",
                "url": "https://{{host}}/api",
            }
            resolved = self.resolver.resolve(variables)
            self.assertEqual("api.prod.company.com", resolved["host"])
            self.assertEqual("https://api.prod.company.com/api", resolved["url"])

    def test_direct_circular_dependency_cycle_detection(self):
        variables = {
            "a": "{{b}}",
            "b": "{{a}}",
        }
        resolved = self.resolver.resolve(variables)
        self.assertIn(resolved["a"], ["{{b}}", "{{a}}"])
        self.assertIn(resolved["b"], ["{{a}}", "{{b}}"])

    def test_self_referential_cycle_detection(self):
        variables = {
            "loop": "{{loop}}",
            "ok": "valid",
        }
        resolved = self.resolver.resolve(variables)
        self.assertEqual("{{loop}}", resolved["loop"])
        self.assertEqual("valid", resolved["ok"])

    def test_indirect_three_node_cycle_detection(self):
        variables = {
            "a": "{{b}}",
            "b": "{{c}}",
            "c": "{{a}}",
            "d": "independent",
        }
        resolved = self.resolver.resolve(variables)
        self.assertEqual("independent", resolved["d"])

    def test_max_depth_exceeded_fallback(self):
        # Build chain of 40 variables
        variables = {f"v{i}": f"{{{{v{i+1}}}}}" for i in range(40)}
        variables["v40"] = "leaf_value"
        resolved = self.resolver.resolve(variables)
        self.assertEqual("leaf_value", resolved["v40"])

    def test_empty_variables_dict(self):
        self.assertEqual({}, self.resolver.resolve({}))

    def test_template_service_resolve_environment_variables_method(self):
        variables = {"a": "1", "b": "{{a}}"}
        resolved = self.template_service.resolve_environment_variables(variables)
        self.assertEqual({"a": "1", "b": "1"}, resolved)

    def test_render_string_automatically_resolves_environment_variables(self):
        variables = {
            "host": "localhost",
            "port": "3000",
            "base_url": "http://{{host}}:{{port}}",
        }
        rendered = self.template_service.render_string("{{base_url}}/items", variables)
        self.assertEqual("http://localhost:3000/items", rendered)

    def test_runtime_and_hover_parity(self):
        with patch.dict(os.environ, {"ENV_PORT": "9090"}):
            variables = {
                "host": "127.0.0.1",
                "port": "{{env(ENV_PORT)}}",
                "server": "{{host}}:{{port}}",
            }
            resolved = self.resolver.resolve(variables)
            for render_path in ("runtime", "hover"):
                with self.subTest(render_path=render_path):
                    res = self.template_service.render_string(
                        "https://{{server}}/status",
                        resolved,
                        render_path=render_path,
                    )
                    self.assertEqual("https://127.0.0.1:9090/status", res)

    def test_curl_generator_with_template_in_env_variables(self):
        variables = {
            "host": "api.example.com",
            "base": "https://{{host}}",
        }
        req = RequestData(url="{{base}}/v1/test", method="GET")
        resolved = self.resolver.resolve(variables)
        curl_cmd = CurlGenerator.generate(req, resolved, self.template_service)
        self.assertIn("https://api.example.com/v1/test", curl_cmd)

    def test_resolve_environment_variables_convenience_function(self):
        variables = {"user": "admin", "greeting": "Hello {{user}}"}
        res = resolve_environment_variables(variables)
        self.assertEqual("Hello admin", res["greeting"])

    def test_http_client_with_template_env_variables(self):
        variables = {
            "domain": "httpbin.org",
            "url_base": "https://{{domain}}",
        }
        client = HTTPClient(template_service=self.template_service)
        req = RequestData(url="{{url_base}}/get", method="GET")
        with patch.object(client.session, "request") as mock_req:
            mock_req.return_value.status_code = 200
            mock_req.return_value.headers = {}
            mock_req.return_value.raw.read.return_value = b""
            mock_req.return_value.iter_content = lambda chunk_size=1: iter([b""])
            res = client.send_request(req, variables=variables)
            self.assertEqual("https://httpbin.org/get", res.resolved.url)

    def test_variable_hover_resolver_with_template_env_variables(self):
        variables = {
            "host": "my-host.internal",
            "port": "8080",
            "base_url": "http://{{host}}:{{port}}",
        }
        resolved_text = VariableHoverResolver.resolve_text("{{base_url}}/api", variables)
        self.assertEqual("http://my-host.internal:8080/api", resolved_text)


if __name__ == "__main__":
    unittest.main()
