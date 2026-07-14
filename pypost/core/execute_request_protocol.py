"""Protocol for full request execution consumed by workers and MCP inbound path."""
from __future__ import annotations

from typing import Any, Callable, Dict, Protocol, runtime_checkable

from pypost.core.request_service import ExecutionResult
from pypost.models.errors import ExecutionError
from pypost.models.models import RequestData


@runtime_checkable
class ExecuteRequestProtocol(Protocol):
    """Execute surface for HTTP/MCP requests — scripts, history, and retries included."""

    def execute(
        self,
        request: RequestData,
        variables: Dict[str, Any] | None = None,
        stream_callback: Callable[[str], None] | None = None,
        stop_flag: Callable[[], bool] | None = None,
        headers_callback: Callable[[int, Dict], None] | None = None,
        collection_name: str | None = None,
        request_name: str | None = None,
        retry_callback: Callable[[int, int, ExecutionError], None] | None = None,
        hidden_keys: set[str] | None = None,
    ) -> ExecutionResult: ...
