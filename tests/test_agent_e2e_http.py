"""Unit tests for agent e2e HTTP canned catalog / stub (PYPOST-859)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pypost.core import request_service
from pypost.fixtures.agent_e2e_http import (
    CANNED_DOUBLE_BODY_LOCK_OK,
    CANNED_GOLDEN_OK,
    CANNED_HTTP_CATALOG,
    CANNED_SEED_GET_OK,
    CANNED_SEED_POST_OK,
    GOLDEN_BODY,
    GOLDEN_URL,
    LOCK_DOUBLE_BODY,
    LOCK_DOUBLE_BODY_URL,
    SEND_REQUEST_PATCH_TARGET,
    SEED_GET_OK_BODY,
    SEED_GET_RESOLVED_URL,
    canned_send_with_one_chunk,
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
        "double_body_lock_ok",
    }
    assert CANNED_HTTP_CATALOG["golden_ok"] is CANNED_GOLDEN_OK
    assert CANNED_GOLDEN_OK.response.body == GOLDEN_BODY
    assert CANNED_GOLDEN_OK.resolved.url == GOLDEN_URL
    assert CANNED_SEED_GET_OK.resolved.url == SEED_GET_RESOLVED_URL
    assert CANNED_SEED_GET_OK.response.body == SEED_GET_OK_BODY
    assert CANNED_SEED_POST_OK.response.status_code == 200
    assert CANNED_HTTP_CATALOG["double_body_lock_ok"] is CANNED_DOUBLE_BODY_LOCK_OK
    assert CANNED_DOUBLE_BODY_LOCK_OK.resolved.url == LOCK_DOUBLE_BODY_URL
    assert CANNED_DOUBLE_BODY_LOCK_OK.response.body == LOCK_DOUBLE_BODY
    assert (
        CANNED_DOUBLE_BODY_LOCK_OK.response.headers["Content-Type"] == "text/plain"
    )


def test_canned_send_with_one_chunk_invokes_stream_callback() -> None:
    chunks: list[str] = []
    headers_seen: list[tuple[int, dict]] = []
    send = canned_send_with_one_chunk(CANNED_DOUBLE_BODY_LOCK_OK)
    out = send(
        MagicMock(),
        stream_callback=chunks.append,
        headers_callback=lambda s, h: headers_seen.append((s, h)),
    )
    assert out is CANNED_DOUBLE_BODY_LOCK_OK
    assert chunks == [LOCK_DOUBLE_BODY]
    assert headers_seen == [
        (200, dict(CANNED_DOUBLE_BODY_LOCK_OK.response.headers)),
    ]


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
