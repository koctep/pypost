"""Tests for MetricsTrackerProtocol, NullMetrics, and MetricsManager compliance."""

import pytest

from unittest.mock import MagicMock

from pypost.core.qt.metrics import MetricsManager
from pypost.core.metrics_protocol import (
    NULL_METRICS,
    MetricsTrackerProtocol,
    NullMetrics,
    resolve_metrics,
)
from pypost.models.errors import ErrorCategory

pytestmark = pytest.mark.timeout(10)


def test_metrics_manager_satisfies_tracker_protocol():
    assert isinstance(MetricsManager(), MetricsTrackerProtocol)


def test_null_metrics_satisfies_tracker_protocol():
    assert isinstance(NullMetrics(), MetricsTrackerProtocol)
    assert isinstance(NULL_METRICS, MetricsTrackerProtocol)


def test_null_metrics_track_methods_are_no_ops():
    metrics = NullMetrics()
    metrics.track_request_sent("GET")
    metrics.track_request_error(ErrorCategory.NETWORK)
    metrics.set_mcp_server_up(True)


def test_resolve_metrics_returns_null_metrics_when_none():
    assert resolve_metrics(None) is NULL_METRICS


def test_resolve_metrics_returns_injected_tracker():
    mock = MagicMock(spec=MetricsTrackerProtocol)
    assert resolve_metrics(mock) is mock


def test_magic_mock_can_stand_in_for_tracker_protocol():
    mock = MagicMock(spec=MetricsTrackerProtocol)
    mock.track_request_sent("GET")
    mock.track_request_sent.assert_called_once_with("GET")
