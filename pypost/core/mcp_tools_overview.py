import logging
from dataclasses import dataclass

from pypost.core.mcp_tool_contract import normalize_mcp_tool_name, tool_description
from pypost.models.models import Collection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class McpToolOverviewEntry:
    """One row in the MCP tools overview."""

    mcp_name: str
    request_name: str
    collection_name: str
    method: str
    description: str


def collect_mcp_tool_overview(collections: list[Collection]) -> list[McpToolOverviewEntry]:
    """Return exposed MCP tools across all collections, sorted for display."""
    entries: list[McpToolOverviewEntry] = []
    for collection in collections:
        for request in collection.requests:
            if not request.expose_as_mcp:
                continue
            entries.append(
                McpToolOverviewEntry(
                    mcp_name=normalize_mcp_tool_name(request.name),
                    request_name=request.name or "",
                    collection_name=collection.name,
                    method=request.method or "GET",
                    description=tool_description(request),
                )
            )
    entries.sort(key=lambda item: (item.mcp_name, item.collection_name))
    logger.debug("mcp_tools_overview_collected tool_count=%d", len(entries))
    return entries
