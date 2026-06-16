"""Sanitize upstream HTTP bodies and script logs for MCP agent responses (PYPOST-703)."""

from __future__ import annotations

import json
import re
from typing import Any, Iterable, Mapping

from pypost.core.sensitive_data_masking_policy import HIDDEN_PLACEHOLDER

_SENSITIVE_JSON_KEY = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|access[_-]?token|"
    r"refresh[_-]?token|client[_-]?secret|private[_-]?key|session[_-]?id)"
)
_BEARER_TOKEN = re.compile(r"Bearer\s+[^\s\"'<>]+", re.IGNORECASE)
_QUERY_TOKEN = re.compile(
    r"([?&](?:token|access_token|api_key|apikey|key|secret|auth)=)[^&\s\"']+",
    re.IGNORECASE,
)


class McpResponseSanitizer:
    """Redact secrets echoed in upstream responses before agents see them."""

    @staticmethod
    def sanitize_text(
        text: str,
        *,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
    ) -> str:
        if not text:
            return text
        redacted = McpResponseSanitizer._redact_hidden_values(text, env_vars, hidden_keys)
        redacted = McpResponseSanitizer._redact_json_sensitive_fields(redacted)
        redacted = _BEARER_TOKEN.sub(f"Bearer {HIDDEN_PLACEHOLDER}", redacted)
        return _QUERY_TOKEN.sub(rf"\1{HIDDEN_PLACEHOLDER}", redacted)

    @staticmethod
    def sanitize_body(
        body: str,
        *,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
    ) -> str:
        return McpResponseSanitizer.sanitize_text(
            body, env_vars=env_vars, hidden_keys=hidden_keys
        )

    @staticmethod
    def sanitize_logs(
        logs: list[str],
        *,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
    ) -> list[str]:
        return [
            McpResponseSanitizer.sanitize_text(
                line, env_vars=env_vars, hidden_keys=hidden_keys
            )
            for line in logs
        ]

    @staticmethod
    def _redact_hidden_values(
        text: str,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
    ) -> str:
        values = [
            env_vars[key]
            for key in hidden_keys
            if key in env_vars and env_vars[key]
        ]
        for value in sorted(values, key=len, reverse=True):
            text = text.replace(value, HIDDEN_PLACEHOLDER)
        return text

    @staticmethod
    def _redact_json_sensitive_fields(text: str) -> str:
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return text
        redacted = McpResponseSanitizer._redact_json_value(parsed)
        return json.dumps(redacted, ensure_ascii=False)

    @staticmethod
    def _redact_json_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: (
                    HIDDEN_PLACEHOLDER
                    if _SENSITIVE_JSON_KEY.search(str(key))
                    else McpResponseSanitizer._redact_json_value(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [McpResponseSanitizer._redact_json_value(item) for item in value]
        return value
