"""Tests for HTTPClientProtocol and HTTPClient compliance."""

import pytest

from unittest.mock import MagicMock

from pypost.core.http_client import HTTPClient
from pypost.core.http_client_protocol import HTTPClientProtocol
from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService

pytestmark = pytest.mark.timeout(10)


def test_http_client_satisfies_protocol():
    assert isinstance(HTTPClient(), HTTPClientProtocol)


def test_magic_mock_can_stand_in_for_http_client_protocol():
    mock = MagicMock(spec=HTTPClientProtocol)
    svc = RequestService(http_client=mock)
    assert isinstance(svc.http_client, HTTPClientProtocol)


def test_request_service_default_http_client_satisfies_protocol():
    svc = RequestService(template_service=TemplateService())
    assert isinstance(svc.http_client, HTTPClientProtocol)
