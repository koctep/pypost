"""Shared heuristics for redacting secrets in text, headers, and JSON (PYPOST-703/706)."""

from __future__ import annotations

import json
import re
from typing import Any, Iterable, Mapping

HIDDEN_PLACEHOLDER = "***"

_SENSITIVE_JSON_KEY = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|access[_-]?token|"
    r"refresh[_-]?token|client[_-]?secret|private[_-]?key|session[_-]?id)"
)
_BEARER_TOKEN = re.compile(r"Bearer\s+[^\s\"'<>]+", re.IGNORECASE)
_QUERY_TOKEN = re.compile(
    r"([?&](?:token|access_token|api_key|apikey|key|secret|auth)=)[^&\s\"']+",
    re.IGNORECASE,
)
_SENSITIVE_HEADER_NAMES = frozenset(
    name.lower()
    for name in (
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-access-token",
        "api-key",
    )
)


def sanitize_text(
    text: str,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> str:
    """Apply hidden-value and heuristic redactions to plain text."""
    if not text:
        return text
    env = env_vars or {}
    hidden = hidden_keys or ()
    redacted = _redact_hidden_values(text, env, hidden)
    redacted = _redact_json_sensitive_fields(redacted)
    redacted = _BEARER_TOKEN.sub(f"Bearer {HIDDEN_PLACEHOLDER}", redacted)
    return _QUERY_TOKEN.sub(rf"\1{HIDDEN_PLACEHOLDER}", redacted)


def sanitize_headers(
    headers: Mapping[str, str],
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> dict[str, str]:
    """Redact sensitive header values and apply text heuristics."""
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _SENSITIVE_HEADER_NAMES:
            result[key] = HIDDEN_PLACEHOLDER
        else:
            result[key] = sanitize_text(
                value, env_vars=env_vars, hidden_keys=hidden_keys
            )
    return result


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


def _redact_json_sensitive_fields(text: str) -> str:
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text
    redacted = _redact_json_value(parsed)
    return json.dumps(redacted, ensure_ascii=False)


def _redact_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                HIDDEN_PLACEHOLDER
                if _SENSITIVE_JSON_KEY.search(str(key))
                else _redact_json_value(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_json_value(item) for item in value]
    return value
