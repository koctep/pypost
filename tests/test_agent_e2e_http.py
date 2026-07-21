"""Unit tests for agent e2e HTTP canned catalog / stub (PYPOST-859)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pypost.core import request_service
from pypost.fixtures.agent_e2e_http import (
    CANNED_GOLDEN_OK,
    CANNED_HTTP_CATALOG,
    CANNED_SEED_GET_OK,
    CANNED_SEED_POST_OK,
    GOLDEN_BODY,
    GOLDEN_URL,
    SEND_REQUEST_PATCH_TARGET,
    SEED_GET_OK_BODY,
    SEED_GET_RESOLVED_URL,
    make_canned_http_result,
    stub_agent_e2e_http,
)

pytestmark = pytest.mark.timeout(10)


def test_make_canned_http_result_defaults() -> None:
    result = make_canned_http_result(url="https://example.test/x")
    assert result.response.status_code == 200
    assert result.response.body == '{"ok": true}'
    assert result.resolved.url == "https://example.test/x"
    assert result.response.headers["Content-Type"] == "application/json"


def test_canned_catalog_names() -> None:
    assert set(CANNED_HTTP_CATALOG) == {
        "golden_ok",
        "seed_get_ok",
        "seed_post_ok",
    }
    assert CANNED_HTTP_CATALOG["golden_ok"] is CANNED_GOLDEN_OK
    assert CANNED_GOLDEN_OK.response.body == GOLDEN_BODY
    assert CANNED_GOLDEN_OK.resolved.url == GOLDEN_URL
    assert CANNED_SEED_GET_OK.resolved.url == SEED_GET_RESOLVED_URL
    assert CANNED_SEED_GET_OK.response.body == SEED_GET_OK_BODY
    assert CANNED_SEED_POST_OK.response.status_code == 200


def test_stub_agent_e2e_http_return_value_and_restore() -> None:
    original = request_service.HTTPClient.send_request
    with stub_agent_e2e_http(CANNED_GOLDEN_OK):
        assert request_service.HTTPClient.send_request is not original
        client = MagicMock()
        out = request_service.HTTPClient.send_request(client, MagicMock())
        assert out is CANNED_GOLDEN_OK
    assert request_service.HTTPClient.send_request is original


def test_stub_agent_e2e_http_callable_side_effect() -> None:
    calls: list[object] = []

    def _factory(*_args: object, **_kwargs: object) -> object:
        calls.append(1)
        return CANNED_SEED_GET_OK

    with stub_agent_e2e_http(_factory, name="seed_get_factory"):
        out = request_service.HTTPClient.send_request(MagicMock(), MagicMock())
        assert out is CANNED_SEED_GET_OK
    assert calls == [1]


def test_send_request_patch_target_constant() -> None:
    assert SEND_REQUEST_PATCH_TARGET == (
        "pypost.core.request_service.HTTPClient.send_request"
    )
