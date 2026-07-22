"""Deterministic HTTP canned responses for agent e2e (PYPOST-859)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Union
from unittest.mock import patch

from pypost.core.http_client import HTTPRequestResult
from pypost.core.request_fields import ResolvedRequestFields
from pypost.fixtures.agent_e2e_seed import (
    SEED_BASE_URL_VALUE,
    SEED_POST_BODY,
)
from pypost.models.response import ResponseData

logger = logging.getLogger(__name__)

# Patch where RequestService looks up HTTPClient.send_request (use site).
SEND_REQUEST_PATCH_TARGET = (
    "pypost.core.request_service.HTTPClient.send_request"
)

GOLDEN_URL = "https://example.test/agent-golden"
GOLDEN_METHOD = "GET"
GOLDEN_STATUS = 200
GOLDEN_BODY = '{"ok": true}'

SEED_GET_RESOLVED_URL = f"{SEED_BASE_URL_VALUE}/get"
SEED_POST_RESOLVED_URL = f"{SEED_BASE_URL_VALUE}/post"
SEED_GET_OK_BODY = '{"seed": "get", "ok": true}'
SEED_POST_OK_BODY = '{"seed": "post", "ok": true, "echo": true}'

CannedResultOrFactory = Union[
    HTTPRequestResult,
    Callable[..., HTTPRequestResult],
    Mapping[str, HTTPRequestResult],
]


def make_canned_http_result(
    *,
    url: str,
    status_code: int = 200,
    body: str = '{"ok": true}',
    headers: dict[str, str] | None = None,
    elapsed_time: float = 0.01,
    resolved_headers: dict[str, str] | None = None,
    resolved_body: str = "",
) -> HTTPRequestResult:
    """Build an ``HTTPRequestResult`` suitable for ``send_request`` stubs."""
    resp_headers = (
        {"Content-Type": "application/json"} if headers is None else headers
    )
    return HTTPRequestResult(
        response=ResponseData(
            status_code=status_code,
            headers=resp_headers,
            body=body,
            elapsed_time=elapsed_time,
            size=len(body),
        ),
        resolved=ResolvedRequestFields(
            url=url,
            headers=dict(resolved_headers or {}),
            body=resolved_body,
        ),
    )


CANNED_GOLDEN_OK = make_canned_http_result(
    url=GOLDEN_URL,
    status_code=GOLDEN_STATUS,
    body=GOLDEN_BODY,
)

CANNED_SEED_GET_OK = make_canned_http_result(
    url=SEED_GET_RESOLVED_URL,
    body=SEED_GET_OK_BODY,
)

CANNED_SEED_POST_OK = make_canned_http_result(
    url=SEED_POST_RESOLVED_URL,
    body=SEED_POST_OK_BODY,
    resolved_body=SEED_POST_BODY,
)

# PYPOST-889 / PYPOST-887 lock: plain body so snapshot count is stable.
LOCK_DOUBLE_BODY_URL = "https://example.test/pypost-887-double-body"
LOCK_DOUBLE_BODY_METHOD = "PUT"
LOCK_DOUBLE_BODY_REQUEST = '{ { "data": { } } }'
LOCK_DOUBLE_BODY_STATUS = 200
LOCK_DOUBLE_BODY = "pypost-887-lock-body-once"

CANNED_DOUBLE_BODY_LOCK_OK = make_canned_http_result(
    url=LOCK_DOUBLE_BODY_URL,
    status_code=LOCK_DOUBLE_BODY_STATUS,
    body=LOCK_DOUBLE_BODY,
    headers={"Content-Type": "text/plain"},
)

# Name → result for docs and authors extending the catalog.
CANNED_HTTP_CATALOG: dict[str, HTTPRequestResult] = {
    "golden_ok": CANNED_GOLDEN_OK,
    "seed_get_ok": CANNED_SEED_GET_OK,
    "seed_post_ok": CANNED_SEED_POST_OK,
    "double_body_lock_ok": CANNED_DOUBLE_BODY_LOCK_OK,
}


def canned_send_with_one_chunk(
    result: HTTPRequestResult,
) -> Callable[..., HTTPRequestResult]:
    """Build a streaming ``send_request`` stub that emits **one** body chunk.

    Catalog / naming (PYPOST-893): prefer this helper (not a bare
    ``return_value`` stub) whenever an agent e2e scenario must exercise the
    chunk-flush vs ``display_response`` race. The name means: canned HTTP
    result + exactly one ``stream_callback`` invocation with ``resp.body``.

    Stubs that only set ``return_value`` never call ``stream_callback``, so the
    late flush race cannot appear. Double-body lock and presentation-matrix
    flows should always use this helper (see ``CANNED_HTTP_CATALOG`` entries
    and ``doc/dev/agent_e2e_http.md``).

    Signature matches MagicMock ``side_effect`` on a patched method (no
    bound ``self``): positional request plus keyword callbacks.
    """

    def _send(
        *_args: object,
        stream_callback: Callable[[str], None] | None = None,
        headers_callback: Callable[[int, dict], None] | None = None,
        **_kwargs: object,
    ) -> HTTPRequestResult:
        del _args, _kwargs
        resp = result.response
        if headers_callback is not None:
            headers_callback(resp.status_code, dict(resp.headers))
        if stream_callback is not None and resp.body:
            stream_callback(resp.body)
        return result

    return _send


def _request_data_from_send_args(
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> object:
    """Locate ``RequestData`` (or duck-typed stand-in) among send_request args.

    Prefer an arg whose ``url`` is a ``str`` so MagicMock ``self`` (auto-attrs)
    is not mistaken for the request when tests call ``send_request(client, req)``.
    """
    if "request_data" in kwargs:
        return kwargs["request_data"]
    for arg in args:
        url = getattr(arg, "url", None)
        if isinstance(url, str) and hasattr(arg, "method"):
            return arg
    raise AssertionError(
        "agent_e2e_http URL router: could not find request_data with .url/.method"
    )


def url_router_side_effect(
    responses: Mapping[str, HTTPRequestResult],
) -> Callable[..., HTTPRequestResult]:
    """Return a ``send_request`` side_effect that routes by exact request URL.

    Match rule (v1): ``request_data.url`` must equal a map key exactly.
    Unknown URL raises ``AssertionError`` listing known keys.
    """
    known = dict(responses)

    def _send(*args: object, **kwargs: object) -> HTTPRequestResult:
        request_data = _request_data_from_send_args(args, kwargs)
        url = getattr(request_data, "url", "") or ""
        if url not in known:
            raise AssertionError(
                "agent_e2e_http URL router: no canned response for "
                f"url={url!r}; known={sorted(known)}"
            )
        return known[url]

    return _send


@contextmanager
def stub_agent_e2e_http(
    result: CannedResultOrFactory = CANNED_GOLDEN_OK,
    *,
    name: str = "custom",
) -> Iterator[None]:
    """Patch ``HTTPClient.send_request`` at the RequestService import site.

    Pass a canned ``HTTPRequestResult``, a callable used as ``side_effect``,
    or a ``Mapping[str, HTTPRequestResult]`` keyed by exact ``request_data.url``
    (PYPOST-868 URL router). Restores the original binding on exit.
    """
    catalog_name = name
    if result is CANNED_GOLDEN_OK:
        catalog_name = "golden_ok"
    elif result is CANNED_SEED_GET_OK:
        catalog_name = "seed_get_ok"
    elif result is CANNED_SEED_POST_OK:
        catalog_name = "seed_post_ok"
    elif result is CANNED_DOUBLE_BODY_LOCK_OK:
        catalog_name = "double_body_lock_ok"
    elif isinstance(result, Mapping) and not isinstance(result, HTTPRequestResult):
        if name == "custom":
            catalog_name = "url_router"

    logger.info("agent_e2e_http_stub_installed name=%s", catalog_name)
    if isinstance(result, Mapping) and not isinstance(result, HTTPRequestResult):
        router = url_router_side_effect(result)
        with patch(SEND_REQUEST_PATCH_TARGET, side_effect=router):
            yield
    elif callable(result) and not isinstance(result, HTTPRequestResult):
        with patch(SEND_REQUEST_PATCH_TARGET, side_effect=result):
            yield
    else:
        with patch(SEND_REQUEST_PATCH_TARGET, return_value=result):
            yield
