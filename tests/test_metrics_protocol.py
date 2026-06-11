"""Tests that MetricsManager satisfies MetricsTrackerProtocol (PYPOST-73)."""

import pytest

pytestmark = pytest.mark.timeout(10)

from unittest.mock import MagicMock

from pypost.core.metrics import MetricsManager
from pypost.core.metrics_protocol import MetricsTrackerProtocol


def test_metrics_manager_satisfies_tracker_protocol():
    assert isinstance(MetricsManager(), MetricsTrackerProtocol)


def test_magic_mock_can_stand_in_for_tracker_protocol():
    mock = MagicMock(spec=MetricsTrackerProtocol)
    mock.track_request_sent("GET")
    mock.track_request_sent.assert_called_once_with("GET")
