"""Convert legacy HTTP method MCP RequestData to McpClientConnection (PYPOST-1171)."""

from __future__ import annotations

import json
import logging

from pypost.models.mcp_client import McpClientConnection
from pypost.models.models import RequestData

logger = logging.getLogger(__name__)

__all__ = ["is_legacy_mcp_request", "request_data_to_mcp_client"]


def is_legacy_mcp_request(request: RequestData) -> bool:
    """Return True when *request* uses the retired HTTP method MCP."""
    return request.method.upper() == "MCP"


def request_data_to_mcp_client(request: RequestData) -> McpClientConnection:
    """Map method=MCP RequestData to McpClientConnection (body → last_tool_*)."""
    last_tool_name: str | None = None
    last_tool_arguments: dict = {}
    body = (request.body or "").strip()
    if body:
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict) and "name" in parsed:
                last_tool_name = str(parsed["name"])
                arguments = parsed.get("arguments")
                if isinstance(arguments, dict):
                    last_tool_arguments = dict(arguments)
        except json.JSONDecodeError:
            logger.debug(
                "legacy_mcp_body_not_json request_id=%s",
                request.id,
            )

    connection = McpClientConnection(
        id=request.id,
        name=request.name,
        url=request.url,
        headers=dict(request.headers),
        last_tool_name=last_tool_name,
        last_tool_arguments=last_tool_arguments,
    )
    logger.info(
        "legacy_mcp_request_migrated request_id=%s has_tool=%s",
        request.id,
        last_tool_name is not None,
    )
    return connection
