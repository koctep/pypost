"""PYPOST-464: Prometheus counter tests for hidden-value masking metrics."""

import pytest

from unittest.mock import MagicMock

from prometheus_client import generate_latest

from pypost.core.http_client import HTTPRequestResult, ResolvedRequestFields
from pypost.core.history_manager import HistoryManager
from pypost.core.qt.metrics import MetricsManager
from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData
from pypost.models.response import ResponseData

pytestmark = pytest.mark.timeout(60)


HIDDEN_KEY = "token"
HIDDEN_VALUE = "supersecret"
VISIBLE_KEY = "host"
VISIBLE_VALUE = "example.com"

METRIC_LINE = 'hidden_value_masks_applied_total{surface="history"}'


def _scrape_metrics(metrics: MetricsManager) -> str:
    return generate_latest(metrics.registry).decode("utf-8")


def _make_response(status=200, body="OK"):
    return ResponseData(
        status_code=status, headers={}, body=body, elapsed_time=0.1, size=len(body)
    )


def _execute_request(metrics: MetricsManager, hidden_keys) -> str:
    history_manager = MagicMock(spec=HistoryManager)
    svc = RequestService(
        metrics=metrics,
        history_manager=history_manager,
        template_service=TemplateService(),
    )
    svc.http_client = MagicMock()
    svc.http_client.send_request.return_value = HTTPRequestResult(
        response=_make_response(200),
        resolved=ResolvedRequestFields(url="http://example.com", headers={}, body=""),
    )
    req = RequestData(
        method="GET",
        url="http://{{host}}?token={{token}}",
        post_script="",
    )
    svc.execute(
        req,
        variables={HIDDEN_KEY: HIDDEN_VALUE, VISIBLE_KEY: VISIBLE_VALUE},
        hidden_keys=hidden_keys,
    )
    return _scrape_metrics(metrics)


def test_hidden_mask_metric_not_incremented_when_hidden_keys_empty():
    metrics = MetricsManager()
    scraped = _execute_request(metrics, hidden_keys=set())
    assert METRIC_LINE not in scraped


def test_hidden_mask_metric_not_incremented_when_hidden_keys_none():
    metrics = MetricsManager()
    scraped = _execute_request(metrics, hidden_keys=None)
    assert METRIC_LINE not in scraped


def test_hidden_mask_metric_incremented_when_hidden_keys_present():
    metrics = MetricsManager()
    scraped = _execute_request(metrics, hidden_keys={HIDDEN_KEY})
    assert f"{METRIC_LINE} 1.0" in scraped
