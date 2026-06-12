"""Unit tests for bind host/port validation (PYPOST-151)."""

import pytest

from pypost.core.bind_address_validation import (
    BindAddressValidationFailure,
    validate_bind_host,
    validate_bind_port,
)

pytestmark = pytest.mark.timeout(30)


class TestValidateBindHost:
    def test_accepts_ipv4(self):
        assert validate_bind_host("127.0.0.1", field_label="MCP Server Host") == "127.0.0.1"

    def test_accepts_all_interfaces(self):
        assert validate_bind_host("0.0.0.0", field_label="MCP Server Host") == "0.0.0.0"

    def test_accepts_ipv6(self):
        assert validate_bind_host("::1", field_label="MCP Server Host") == "::1"

    def test_accepts_hostname(self):
        assert validate_bind_host("localhost", field_label="MCP Server Host") == "localhost"

    def test_accepts_fqdn(self):
        result = validate_bind_host("api.example.com", field_label="MCP Server Host")
        assert result == "api.example.com"

    def test_strips_whitespace(self):
        assert validate_bind_host("  127.0.0.1  ", field_label="MCP Server Host") == "127.0.0.1"

    def test_rejects_empty(self):
        result = validate_bind_host("   ", field_label="MCP Server Host")
        assert isinstance(result, BindAddressValidationFailure)
        assert result.reason == "empty"
        assert "cannot be empty" in result.message

    def test_rejects_invalid_token(self):
        result = validate_bind_host("not a host!", field_label="MCP Server Host")
        assert isinstance(result, BindAddressValidationFailure)
        assert result.reason == "invalid_format"
        assert "valid IP address" in result.message


class TestValidateBindPort:
    def test_accepts_in_range(self):
        assert validate_bind_port(1080, field_label="MCP Server Port") == 1080

    def test_rejects_below_minimum(self):
        result = validate_bind_port(80, field_label="MCP Server Port")
        assert isinstance(result, BindAddressValidationFailure)
        assert result.reason == "out_of_range"

    def test_rejects_above_maximum(self):
        result = validate_bind_port(70000, field_label="MCP Server Port")
        assert isinstance(result, BindAddressValidationFailure)
        assert result.reason == "out_of_range"
