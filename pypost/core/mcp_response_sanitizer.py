"""Sanitize upstream HTTP bodies and script logs for MCP agent responses (PYPOST-703)."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from pypost.core import sensitive_text_sanitizer as sts


class McpResponseSanitizer:
    """Redact secrets echoed in upstream responses before agents see them."""

    @staticmethod
    def sanitize_text(
        text: str,
        *,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
    ) -> str:
        return sts.sanitize_text(text, env_vars=env_vars, hidden_keys=hidden_keys)

    @staticmethod
    def sanitize_body(
        body: str,
        hidden_fields: Sequence[str] | Iterable[str] | None = None,
        *,
        env_vars: Mapping[str, str] | None = None,
        hidden_keys: Iterable[str] | None = None,
        hidden_response_fields: Sequence[str] | Iterable[str] | None = None,
    ) -> str:
        """Sanitizes HTTP body for MCP tool output, redacting hidden fields and env secrets."""
        fields = (
            hidden_response_fields
            if hidden_response_fields is not None
            else hidden_fields
        )
        if fields:
            body = sts.redact_json_response_fields(body, fields)
        return sts.sanitize_text(body, env_vars=env_vars, hidden_keys=hidden_keys)

    @staticmethod
    def sanitize_logs(
        logs: list[str],
        *,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
    ) -> list[str]:
        return [
            sts.sanitize_text(line, env_vars=env_vars, hidden_keys=hidden_keys)
            for line in logs
        ]
