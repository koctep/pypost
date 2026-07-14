"""Protocol for HTTP transport consumed by RequestService."""
from __future__ import annotations

from typing import Callable, Dict, Protocol, runtime_checkable

from pypost.core.http_client import HTTPRequestResult
from pypost.models.models import RequestData


@runtime_checkable
class HTTPClientProtocol(Protocol):
    """Send-request surface for HTTP execution — no session or template lifecycle."""

    def send_request(
        self,
        request_data: RequestData,
        variables: Dict[str, str] | None = None,
        stream_callback: Callable[[str], None] | None = None,
        stop_flag: Callable[[], bool] | None = None,
        headers_callback: Callable[[int, Dict], None] | None = None,
    ) -> HTTPRequestResult: ...
