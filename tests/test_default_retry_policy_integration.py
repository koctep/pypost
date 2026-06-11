"""Integration tests for default_retry_policy DI chain (PYPOST-440)."""

import pytest

pytestmark = pytest.mark.timeout(120)

import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from pypost.core.http_client import HTTPRequestResult, ResolvedRequestFields
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.models.retry import RetryPolicy
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter

from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager


def _http_result(status_code: int) -> HTTPRequestResult:
    body = str(status_code)
    return HTTPRequestResult(
        response=ResponseData(
            status_code=status_code,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body),
        ),
        resolved=ResolvedRequestFields(url="http://example.com", headers={}, body=""),
    )


class TestDefaultRetryPolicyIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tabs_presenter_forwards_app_default_retry_policy_to_worker(self):
        policy = RetryPolicy(max_retries=2, retryable_status_codes=[500])
        settings = AppSettings(default_retry_policy=policy)
        presenter = TabsPresenter(
            FakeRequestManager(),
            FakeStateManager(),
            settings,
            metrics=MagicMock(),
        )
        presenter.add_new_tab(save_state=False)
        tab = presenter.widget.currentWidget()
        self.assertIsInstance(tab, RequestTab)

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as mock_worker_cls:
            mock_worker = MagicMock()
            mock_worker_cls.return_value = mock_worker
            tab.request_editor.send_requested.emit(tab.request_editor.request_data)

        mock_worker_cls.assert_called_once()
        self.assertIs(
            mock_worker_cls.call_args.kwargs["default_retry_policy"],
            policy,
        )

    def test_worker_applies_app_default_retry_policy_on_send(self):
        policy = RetryPolicy(max_retries=1, retryable_status_codes=[500])
        settings = AppSettings(default_retry_policy=policy)
        presenter = TabsPresenter(
            FakeRequestManager(),
            FakeStateManager(),
            settings,
            metrics=MagicMock(),
        )
        presenter.add_new_tab(save_state=False)
        tab = presenter.widget.currentWidget()
        self.assertIsInstance(tab, RequestTab)

        with patch(
            "pypost.core.request_service.HTTPClient.send_request",
            side_effect=[_http_result(500), _http_result(200)],
        ) as mock_send:
            tab.request_editor.send_requested.emit(tab.request_editor.request_data)
            tab.worker.wait(5000)

        self.assertEqual(2, mock_send.call_count)
