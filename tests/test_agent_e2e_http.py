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
    SEED_POST_RESOLVED_URL,
    canned_send_with_one_chunk,
    make_canned_http_result,
    stub_agent_e2e_http,
)
from pypost.models.models import RequestData

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


def test_stub_agent_e2e_http_url_router_map() -> None:
    """PYPOST-868: Mapping[url → canned] routes each send by request URL."""
    responses = {
        SEED_GET_RESOLVED_URL: CANNED_SEED_GET_OK,
        SEED_POST_RESOLVED_URL: CANNED_SEED_POST_OK,
    }
    get_req = RequestData(method="GET", url=SEED_GET_RESOLVED_URL)
    post_req = RequestData(method="POST", url=SEED_POST_RESOLVED_URL)
    original = request_service.HTTPClient.send_request

    with stub_agent_e2e_http(responses, name="url_router"):
        assert request_service.HTTPClient.send_request is not original
        client = MagicMock()
        assert (
            request_service.HTTPClient.send_request(client, get_req)
            is CANNED_SEED_GET_OK
        )
        assert (
            request_service.HTTPClient.send_request(client, post_req)
            is CANNED_SEED_POST_OK
        )
    assert request_service.HTTPClient.send_request is original


def test_stub_agent_e2e_http_url_router_miss_raises() -> None:
    """PYPOST-868: unknown URL fails loudly with known keys listed."""
    responses = {SEED_GET_RESOLVED_URL: CANNED_SEED_GET_OK}
    unknown = RequestData(method="GET", url="https://example.test/missing")

    with stub_agent_e2e_http(responses, name="url_router"):
        with pytest.raises(AssertionError, match=r"missing|known") as exc_info:
            request_service.HTTPClient.send_request(MagicMock(), unknown)
    message = str(exc_info.value)
    assert "https://example.test/missing" in message
    assert SEED_GET_RESOLVED_URL in message


def test_stub_agent_e2e_http_url_router_method_url_compound_keys() -> None:
    """PYPOST-902: compound method+URL keys route same URL by HTTP method."""
    shared_url = "https://example.test/shared"
    get_result = make_canned_http_result(
        url=shared_url,
        body='{"via": "get"}',
    )
    post_result = make_canned_http_result(
        url=shared_url,
        body='{"via": "post"}',
    )
    responses = {
        f"GET {shared_url}": get_result,
        f"POST {shared_url}": post_result,
    }
    get_req = RequestData(method="GET", url=shared_url)
    post_req = RequestData(method="POST", url=shared_url)

    with stub_agent_e2e_http(responses, name="url_router"):
        client = MagicMock()
        assert (
            request_service.HTTPClient.send_request(client, get_req) is get_result
        )
        assert (
            request_service.HTTPClient.send_request(client, post_req)
            is post_result
        )


def test_stub_agent_e2e_http_url_router_compound_precedence_over_bare_url() -> None:
    """PYPOST-902: compound key wins over bare URL when both exist."""
    shared_url = "https://example.test/precedence"
    compound_result = make_canned_http_result(
        url=shared_url,
        body='{"via": "compound"}',
    )
    bare_result = make_canned_http_result(
        url=shared_url,
        body='{"via": "bare"}',
    )
    responses = {
        f"GET {shared_url}": compound_result,
        shared_url: bare_result,
    }
    get_req = RequestData(method="GET", url=shared_url)

    with stub_agent_e2e_http(responses, name="url_router"):
        out = request_service.HTTPClient.send_request(MagicMock(), get_req)
        assert out is compound_result
        assert out.response.body == '{"via": "compound"}'


def test_send_request_patch_target_constant() -> None:
    assert SEND_REQUEST_PATCH_TARGET == (
        "pypost.core.request_service.HTTPClient.send_request"
    )


def test_seed_post_gui_send_scenario_module_exists() -> None:
    """PYPOST-871: seed POST GUI Send scenario module must exist."""
    import importlib

    mod = importlib.import_module("tests.test_agent_e2e_http_seed_post")
    assert callable(
        getattr(mod, "test_seed_post_send_uses_shared_http_stub", None)
    )


def test_mapping_multi_url_gui_send_scenario_module_exists() -> None:
    """PYPOST-901: GUI multi-URL Mapping Send scenario module must exist."""
    import importlib

    mod = importlib.import_module("tests.test_agent_e2e_http_mapping_multi_url")
    assert callable(
        getattr(mod, "test_mapping_stub_two_distinct_urls_panel_outcomes", None)
    )


def test_mapping_multi_url_settle_timeout_companion_exists() -> None:
    """PYPOST-955: mapping Send settle timeout companion must exist."""
    import importlib

    mod = importlib.import_module(
        "tests.test_agent_e2e_http_mapping_multi_url"
    )
    assert callable(
        getattr(
            mod,
            "test_mapping_get_send_settle_timeout_includes_step_and_excerpt",
            None,
        )
    )
