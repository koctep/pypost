"""IPC message helpers for MCP process-mode workers (PYPOST-1439)."""

from __future__ import annotations

from typing import Any, Literal

MSG_V = 1
SUPPORTED_MSG_VERSIONS = frozenset({MSG_V})


class McpProtocolVersionError(ValueError):
    """Raised when an IPC message has an invalid or unsupported protocol version."""

    def __init__(
        self,
        message: str,
        *,
        received_v: Any = None,
        supported_versions: frozenset[int] | set[int] = SUPPORTED_MSG_VERSIONS,
    ) -> None:
        super().__init__(message)
        self.received_v = received_v
        self.supported_versions = supported_versions


def validate_message_version(message: dict[str, Any]) -> int:
    """Validate that an IPC envelope has a supported integer protocol version.

    Returns:
        The validated integer protocol version.

    Raises:
        McpProtocolVersionError: If "v" is missing, not an int (or is a bool),
            or not in SUPPORTED_MSG_VERSIONS.
    """
    if not isinstance(message, dict) or "v" not in message:
        raise McpProtocolVersionError(
            "IPC message missing required 'v' protocol version field",
            received_v=None,
            supported_versions=SUPPORTED_MSG_VERSIONS,
        )
    v = message["v"]
    if isinstance(v, bool) or not isinstance(v, int):
        raise McpProtocolVersionError(
            f"IPC message version must be an int, got {type(v).__name__}: {v!r}",
            received_v=v,
            supported_versions=SUPPORTED_MSG_VERSIONS,
        )
    if v not in SUPPORTED_MSG_VERSIONS:
        raise McpProtocolVersionError(
            f"Unsupported IPC protocol version {v} (supported: {sorted(SUPPORTED_MSG_VERSIONS)})",
            received_v=v,
            supported_versions=SUPPORTED_MSG_VERSIONS,
        )
    return int(v)


MsgType = Literal[
    "START",
    "UPDATE_TOOLS",
    "UPDATE_VARIABLES",
    "HEARTBEAT",
    "STOP",
    "DEBUG_ABORT",
    "DEBUG_HANG",
    "STARTED",
    "START_FAILED",
    "HEARTBEAT_PONG",
    "ACK",
    "WORKER_ERROR",
    "EXITED",
    "VERSION_MISMATCH",
]


def make_message(msg_type: MsgType, **payload: Any) -> dict[str, Any]:
    """Build a versioned IPC envelope."""
    return {"v": MSG_V, "type": msg_type, **payload}


def message_type(message: dict[str, Any]) -> str:
    """Return the message type string (empty if missing)."""
    raw = message.get("type")
    return str(raw) if raw is not None else ""


def encode_tools(tools: list[Any]) -> list[dict[str, Any]]:
    """Serialize RequestData / WebSocketConnection models to JSON-safe dicts."""
    encoded: list[dict[str, Any]] = []
    for tool in tools:
        dump = getattr(tool, "model_dump", None)
        if callable(dump):
            data = dump(mode="json")
            # Tag so the worker can rebuild the correct model type.
            if tool.__class__.__name__ == "WebSocketConnection":
                data["__mcp_tool_kind__"] = "websocket"
            else:
                data["__mcp_tool_kind__"] = "http"
            encoded.append(data)
        elif isinstance(tool, dict):
            encoded.append(dict(tool))
        else:
            raise TypeError(f"Cannot encode MCP tool of type {type(tool)!r}")
    return encoded


def decode_tools(payload: list[dict[str, Any]]) -> list[Any]:
    """Rebuild tool models from START payload dicts."""
    from pypost.models.models import RequestData
    from pypost.models.websocket import WebSocketConnection

    tools: list[Any] = []
    for item in payload:
        data = dict(item)
        kind = data.pop("__mcp_tool_kind__", "http")
        if kind == "websocket":
            tools.append(WebSocketConnection.model_validate(data))
        else:
            tools.append(RequestData.model_validate(data))
    return tools
