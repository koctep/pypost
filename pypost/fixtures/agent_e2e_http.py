"""Deterministic HTTP canned responses for agent e2e (PYPOST-859)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
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

# Name → result for docs and authors extending the catalog.
CANNED_HTTP_CATALOG: dict[str, HTTPRequestResult] = {
    "golden_ok": CANNED_GOLDEN_OK,
    "seed_get_ok": CANNED_SEED_GET_OK,
    "seed_post_ok": CANNED_SEED_POST_OK,
}


@contextmanager
def stub_agent_e2e_http(
    result: CannedResultOrFactory = CANNED_GOLDEN_OK,
    *,
    name: str = "custom",
) -> Iterator[None]:
    """Patch ``HTTPClient.send_request`` at the RequestService import site.

    Pass a canned ``HTTPRequestResult`` or a callable used as ``side_effect``.
    Restores the original binding on exit (test isolation).
    """
    catalog_name = name
    if result is CANNED_GOLDEN_OK:
        catalog_name = "golden_ok"
    elif result is CANNED_SEED_GET_OK:
        catalog_name = "seed_get_ok"
    elif result is CANNED_SEED_POST_OK:
        catalog_name = "seed_post_ok"

    logger.info("agent_e2e_http_stub_installed name=%s", catalog_name)
    if callable(result) and not isinstance(result, HTTPRequestResult):
        with patch(SEND_REQUEST_PATCH_TARGET, side_effect=result):
            yield
    else:
        with patch(SEND_REQUEST_PATCH_TARGET, return_value=result):
            yield
