import pytest

from unittest.mock import patch
from pypost.core.curl_generator import CurlGenerator
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData, HistoryEntry

pytestmark = pytest.mark.timeout(30)


def test_curl_generator_basic():
    request = RequestData(
        method="GET",
        url="https://api.example.com/users",
        headers={"Accept": "application/json"},
    )
    template_service = TemplateService()

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert curl_cmd == "curl -X GET https://api.example.com/users -H 'Accept: application/json'"

    with patch("sys.platform", "win32"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert curl_cmd == 'curl -X GET https://api.example.com/users -H "Accept: application/json"'


def test_curl_generator_with_params():
    request = RequestData(
        method="GET",
        url="https://api.example.com/users?foo=bar",
        params={"page": "2", "limit": "10"},
    )
    template_service = TemplateService()

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert curl_cmd == "curl -X GET 'https://api.example.com/users?foo=bar&page=2&limit=10'"

    with patch("sys.platform", "win32"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert curl_cmd == 'curl -X GET https://api.example.com/users?foo=bar&page=2&limit=10'


def test_curl_generator_with_body():
    request = RequestData(
        method="POST",
        url="https://api.example.com/users",
        headers={"Content-Type": "application/json"},
        body='{"name": "test"}',
    )
    template_service = TemplateService()

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert curl_cmd == (
            "curl -X POST https://api.example.com/users "
            "-H 'Content-Type: application/json' "
            '-d \'{"name": "test"}\''
        )

    with patch("sys.platform", "win32"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert curl_cmd == (
            'curl -X POST https://api.example.com/users '
            '-H "Content-Type: application/json" '
            '-d "{\\"name\\": \\"test\\"}"'
        )


def test_curl_generator_with_variables():
    request = RequestData(
        method="POST",
        url="{{base_url}}/users",
        headers={"Authorization": "Bearer {{token}}"},
        body='{"name": "{{name}}"}',
    )
    variables = {"base_url": "https://api.example.com", "token": "secret123", "name": "john_doe"}
    template_service = TemplateService()

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate(request, variables, template_service)
        assert curl_cmd == (
            "curl -X POST https://api.example.com/users "
            "-H 'Authorization: Bearer secret123' "
            '-d \'{"name": "john_doe"}\''
        )

    with patch("sys.platform", "win32"):
        curl_cmd = CurlGenerator.generate(request, variables, template_service)
        assert curl_cmd == (
            'curl -X POST https://api.example.com/users '
            '-H "Authorization: Bearer secret123" '
            '-d "{\\"name\\": \\"john_doe\\"}"'
        )


def test_curl_generator_with_complex_body():
    request = RequestData(
        method="POST",
        url="https://api.example.com/users",
        body='{"name": "test",\n"description": "multi\\nline"}',
    )
    template_service = TemplateService()

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        expected = (
            "curl -X POST https://api.example.com/users "
            '-d \'{"name": "test",\n"description": "multi\\nline"}\''
        )
        assert curl_cmd == expected

    with patch("sys.platform", "win32"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        expected = (
            'curl -X POST https://api.example.com/users '
            '-d "{\\"name\\": \\"test\\",\n\\"description\\": \\"multi\\nline\\"}"'
        )
        assert curl_cmd == expected


def test_curl_generator_yaml_as_json_exports_json_wire_body():
    request = RequestData(
        method="POST",
        url="https://api.example.com/users",
        body_type="yaml",
        yaml_as_json=True,
        body="name: test\nid: 1\n",
    )
    template_service = TemplateService()

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert "-d" in curl_cmd
        assert "name" in curl_cmd
        assert "test" in curl_cmd
        assert "name:" not in curl_cmd


def test_curl_generator_yaml_without_flag_keeps_yaml_body():
    request = RequestData(
        method="POST",
        url="https://api.example.com/users",
        body_type="yaml",
        yaml_as_json=False,
        body="name: test\n",
    )
    template_service = TemplateService()

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate(request, {}, template_service)
        assert "name: test" in curl_cmd


def test_curl_generator_from_history():
    entry = HistoryEntry(
        id="123",
        method="POST",
        url="https://api.example.com/data",
        headers={"Content-Type": "application/json", "X-Custom": "value"},
        body='{"key": "value"}',
        status_code=200,
        response_time_ms=50,
        timestamp="2023-01-01T12:00:00Z"
    )

    with patch("sys.platform", "linux"):
        curl_cmd = CurlGenerator.generate_from_history(entry)
        expected = (
            "curl -X POST https://api.example.com/data "
            "-H 'Content-Type: application/json' "
            "-H 'X-Custom: value' "
            "-d '{\"key\": \"value\"}'"
        )
        assert curl_cmd == expected

    with patch("sys.platform", "win32"):
        curl_cmd = CurlGenerator.generate_from_history(entry)
        expected = (
            'curl -X POST https://api.example.com/data '
            '-H "Content-Type: application/json" '
            '-H "X-Custom: value" '
            '-d "{\\"key\\": \\"value\\"}"'
        )
        assert curl_cmd == expected
