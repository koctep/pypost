"""Multi-format WebSocket payload encoders, decoders, and validators (PYPOST-1130).

Provides bidirectional conversion between wire bytes/strings and user presentation
formats (TEXT, JSON, HEX, BASE64) with strict format validation.
"""

from __future__ import annotations

import base64
import binascii
import json

from pypost.models.websocket import WsMessageFormat

__all__ = [
    "encode_payload",
    "decode_payload",
    "detect_binary_presentation",
    "validate_format",
]


def encode_payload(data: str, format: WsMessageFormat | str) -> bytes | str:
    """Encode user input data into the specified WebSocket message format."""
    fmt = WsMessageFormat(format) if isinstance(format, str) else format
    if fmt == WsMessageFormat.TEXT:
        return data
    if fmt == WsMessageFormat.JSON:
        try:
            json.loads(data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        return data
    if fmt == WsMessageFormat.HEX:
        try:
            return bytes.fromhex(data.strip())
        except ValueError as exc:
            raise ValueError(f"Invalid hexadecimal payload: {exc}") from exc
    if fmt == WsMessageFormat.BASE64:
        try:
            return base64.b64decode(data.strip(), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"Invalid Base64 payload: {exc}") from exc
    raise ValueError(f"Unsupported format: {format}")


def decode_payload(payload: bytes | str, format: WsMessageFormat | str) -> str:
    """Decode raw frame payload to display string presentation."""
    fmt = WsMessageFormat(format) if isinstance(format, str) else format
    if fmt == WsMessageFormat.TEXT or fmt == WsMessageFormat.JSON:
        if isinstance(payload, bytes):
            return payload.decode("utf-8", errors="replace")
        return str(payload)
    if fmt == WsMessageFormat.HEX:
        if isinstance(payload, bytes):
            return payload.hex()
        return str(payload)
    if fmt == WsMessageFormat.BASE64:
        if isinstance(payload, bytes):
            return base64.b64encode(payload).decode("ascii")
        return str(payload)
    if isinstance(payload, bytes):
        return payload.decode("utf-8", errors="replace")
    return str(payload)


def detect_binary_presentation(payload: bytes) -> WsMessageFormat:
    """Detect default display format for incoming binary frame."""
    return WsMessageFormat.HEX


def validate_format(data: str, format: WsMessageFormat | str) -> tuple[bool, str | None]:
    """Validate data syntax against format.

    Returns:
        Tuple of (is_valid, error_message_or_None).
    """
    fmt = WsMessageFormat(format) if isinstance(format, str) else format
    if fmt == WsMessageFormat.TEXT:
        return True, None
    if fmt == WsMessageFormat.JSON:
        try:
            json.loads(data)
            return True, None
        except json.JSONDecodeError as exc:
            return False, f"Invalid JSON: {exc.msg} (line {exc.lineno}, col {exc.colno})"
        except Exception as exc:
            return False, f"Invalid JSON: {exc}"
    if fmt == WsMessageFormat.HEX:
        try:
            bytes.fromhex(data.strip())
            return True, None
        except ValueError:
            return False, "Invalid hexadecimal payload: odd number of digits or non-hex characters"
    if fmt == WsMessageFormat.BASE64:
        try:
            base64.b64decode(data.strip(), validate=True)
            return True, None
        except (binascii.Error, ValueError):
            return False, "Invalid Base64 payload: incorrect padding or invalid characters"
    return False, f"Unsupported format: {format}"
