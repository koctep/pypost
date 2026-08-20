"""Tests for request_persisted_fields copy policy and comparison helpers."""

import pytest

import unittest

from pypost.core.request_persisted_fields import (
    copy_request_for_isolated_tab,
    snapshot_persisted_fields,
)
from pypost.models.models import RequestData

pytestmark = pytest.mark.timeout(120)


def _make_request(
    request_id: str = "r1",
    name: str = "Test",
    method: str = "GET",
    url: str = "https://example.com",
) -> RequestData:
    return RequestData(id=request_id, name=name, method=method, url=url)


class TestCopyRequestForIsolatedTab(unittest.TestCase):
    def test_deep_copies_nested_headers(self):
        req = _make_request()
        req.headers = {"X-Test": "1"}
        copy = copy_request_for_isolated_tab(req)
        self.assertIsNot(copy, req)
        copy.headers["X-Test"] = "2"
        self.assertEqual(req.headers["X-Test"], "1")

    def test_deep_copies_body(self):
        req = _make_request()
        req.body = '{"a": 1}'
        copy = copy_request_for_isolated_tab(req)
        copy.body = '{"a": 2}'
        self.assertEqual(req.body, '{"a": 1}')

    def test_snapshot_persisted_fields_uses_same_copy_semantics(self):
        req = _make_request()
        req.params = {"q": "1"}
        snap = snapshot_persisted_fields(req)
        self.assertIsNot(snap, req)
        snap.params["q"] = "2"
        self.assertEqual(req.params["q"], "1")


class TestRequestDataLeanModel(unittest.TestCase):
    """Regression guard: RequestData must not absorb heavy runtime payloads."""

    _FORBIDDEN_FIELD_NAMES = frozenset(
        {
            "response_body",
            "response_headers",
            "response_time_ms",
            "status_code",
            "history",
            "response_view",
        }
    )

    def test_model_fields_exclude_response_and_history_payloads(self):
        field_names = set(RequestData.model_fields)
        overlap = field_names & self._FORBIDDEN_FIELD_NAMES
        self.assertEqual(
            overlap,
            set(),
            f"RequestData must stay lean; remove heavy fields: {sorted(overlap)}",
        )
