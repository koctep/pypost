"""Tests for ExecuteRequestProtocol and RequestService compliance."""

import pytest

pytestmark = pytest.mark.timeout(10)

from unittest.mock import MagicMock

from pypost.core.execute_request_protocol import ExecuteRequestProtocol
from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService
from pypost.core.worker import RequestWorker
from pypost.models.models import RequestData


def test_request_service_satisfies_protocol():
    assert isinstance(RequestService(template_service=TemplateService()), ExecuteRequestProtocol)


def test_magic_mock_can_stand_in_for_execute_request_protocol():
    mock = MagicMock(spec=ExecuteRequestProtocol)
    assert isinstance(mock, ExecuteRequestProtocol)


def test_request_worker_default_executor_satisfies_protocol():
    worker = RequestWorker(RequestData(name="t", method="GET", url="http://example.com"))
    assert isinstance(worker.service, ExecuteRequestProtocol)
