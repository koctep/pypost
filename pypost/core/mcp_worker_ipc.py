"""IPC message helpers for MCP process-mode workers (PYPOST-1439)."""

from __future__ import annotations

from typing import Any, Literal

MSG_V = 1

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
