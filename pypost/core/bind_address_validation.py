"""Validation for MCP and metrics bind host/port settings."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import Union

_BIND_PORT_MIN = 1024
_BIND_PORT_MAX = 65535

_HOSTNAME_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
    r"(?:\.(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?))*$",
)


@dataclass(frozen=True)
class BindAddressValidationFailure:
    """Structured failure from bind host/port validation."""

    field: str
    reason: str
    message: str


def validate_bind_host(raw: str, *, field_label: str) -> Union[str, BindAddressValidationFailure]:
    """Return stripped host or a validation failure."""
    stripped = raw.strip()
    if not stripped:
        return BindAddressValidationFailure(
            field=field_label,
            reason="empty",
            message=(
                f"{field_label} cannot be empty. Enter an IP address "
                "(e.g. 127.0.0.1, 0.0.0.0) or hostname."
            ),
        )
    try:
        ipaddress.ip_address(stripped)
        return stripped
    except ValueError:
        pass
    if _HOSTNAME_RE.fullmatch(stripped):
        return stripped
    return BindAddressValidationFailure(
        field=field_label,
        reason="invalid_format",
        message=(
            f"{field_label} must be a valid IP address "
            "(e.g. 127.0.0.1, 0.0.0.0) or hostname."
        ),
    )


def is_localhost_bind_host(host: str) -> bool:
    """True when the bind address is loopback-only (safe default for metrics/MCP)."""
    stripped = host.strip().lower()
    if stripped in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        return ipaddress.ip_address(stripped).is_loopback
    except ValueError:
        return False


def validate_bind_port(port: int, *, field_label: str) -> Union[int, BindAddressValidationFailure]:
    """Return port or a validation failure."""
    if port < _BIND_PORT_MIN or port > _BIND_PORT_MAX:
        return BindAddressValidationFailure(
            field=field_label,
            reason="out_of_range",
            message=(
                f"{field_label} must be between {_BIND_PORT_MIN} and {_BIND_PORT_MAX}."
            ),
        )
    return port
