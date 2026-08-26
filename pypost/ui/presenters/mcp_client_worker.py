"""One-shot QThread for MCP Client list_tools (already-resolved URL/headers)."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QThread, Signal

from pypost.core.mcp_client_service import MCPClientService
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.response import ResponseData

logger = logging.getLogger(__name__)

__all__ = ["McpClientOutboundWorker"]


class McpClientOutboundWorker(QThread):
    """Call MCPClientService.run off the GUI thread. No widget or resolve access."""

    finished_ok = Signal(int, str, object)
    finished_error = Signal(int, str, object)

    def __init__(
        self,
        client: MCPClientService,
        url: str,
        headers: dict[str, str],
        operation: str,
        call_params: dict[str, Any] | None,
        generation: int,
        kind: str,
    ) -> None:
        super().__init__()
        self._client = client
        self._url = url
        self._headers = dict(headers)
        self._operation = operation
        self._call_params = call_params
        self._generation = generation
        self._kind = kind

    def run(self) -> None:
        logger.debug(
            "mcp_client_outbound_worker_started generation=%s kind=%s",
            self._generation,
            self._kind,
        )
        try:
            result: ResponseData = self._client.run(
                self._url,
                self._operation,
                self._call_params,
                headers=self._headers,
            )
        except ExecutionError as err:
            self.finished_error.emit(self._generation, self._kind, err)
            return
        except Exception as exc:
            logger.error(
                "mcp_client_outbound_worker_unexpected generation=%s kind=%s",
                self._generation,
                self._kind,
                exc_info=True,
            )
            self.finished_error.emit(
                self._generation,
                self._kind,
                ExecutionError(
                    category=ErrorCategory.UNKNOWN,
                    message="An unexpected error occurred.",
                    detail=str(exc),
                ),
            )
            return
        self.finished_ok.emit(self._generation, self._kind, result)
