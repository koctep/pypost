"""Validation policy for MCP endpoint configuration and referenced records."""

from __future__ import annotations

import socket
from collections.abc import Callable, Iterable

from pypost.models.models import Collection, Environment
from pypost.models.settings import McpServerConfiguration


def validate_available_port(
    configuration: McpServerConfiguration,
    existing_configurations: Iterable[McpServerConfiguration],
) -> None:
    """Reject a port already reserved by another persisted endpoint."""
    for existing in existing_configurations:
        if existing.id != configuration.id and existing.port == configuration.port:
            raise ValueError(
                f"MCP server port {configuration.port} is already used by {existing.id}"
            )


def validate_references(
    configuration: McpServerConfiguration,
    *,
    collection_lookup: Callable[[str], Collection | None],
    environment_lookup: Callable[[str], Environment | None],
) -> None:
    """Validate stable IDs before a live endpoint is disturbed."""
    if configuration.server_type == "local" and (
        not configuration.collection_id
        or collection_lookup(configuration.collection_id) is None
    ):
        raise ValueError(
            f"MCP server {configuration.id} references a missing collection"
        )
    if (
        configuration.environment_id
        and environment_lookup(configuration.environment_id) is None
    ):
        raise ValueError(
            f"MCP server {configuration.id} references a missing environment"
        )


def validate_bind_available(host: str, port: int) -> None:
    """Preflight an external bind conflict without owning a server runtime."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind((host, port))
    except OSError as exc:
        raise ValueError(f"MCP server port {port} is unavailable: {exc}") from exc
