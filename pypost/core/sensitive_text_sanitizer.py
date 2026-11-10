"""Shared heuristics for redacting secrets in text, headers, and JSON (PYPOST-703/706)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterable, Mapping, Sequence

from pypost.core.header_selector_prefix import header_selector_name
from pypost.core.json_selector_engine import JsonSelectorEngine, MaskBreadcrumb

logger = logging.getLogger(__name__)

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
    hidden_response_fields: Iterable[str] | None = None,
) -> dict[str, str]:
    """Redact sensitive header values and apply text heuristics."""
    extra_hidden: set[str] = set()
    if hidden_response_fields:
        for field in hidden_response_fields:
            name = header_selector_name(field)
            if name is not None:
                extra_hidden.add(name.strip().lower())
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _SENSITIVE_HEADER_NAMES or key.lower() in extra_hidden:
            result[key] = HIDDEN_PLACEHOLDER
        else:
            result[key] = sanitize_text(
                value, env_vars=env_vars, hidden_keys=hidden_keys
            )
    return result


def redact_json_response_fields(
    body: str,
    hidden_fields: Sequence[str] | Iterable[str] | None = None,
    placeholder: str = HIDDEN_PLACEHOLDER,
) -> str:
    """Recursively redacts configured keys and selector paths in JSON response text."""
    if not body or not hidden_fields:
        return body
    engine = JsonSelectorEngine(hidden_fields)
    if engine.is_empty:
        return body
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.debug(
            "redact_json_response_fields_skipped_non_json reason=%s",
            type(exc).__name__,
        )
        return body
    if not isinstance(parsed, (dict, list)):
        logger.debug(
            "redact_json_response_fields_skipped_non_container type=%s",
            type(parsed).__name__,
        )
        return body
    redacted, masked_count = engine.redact_tree(parsed, placeholder=placeholder)
    logger.debug(
        "redact_json_response_fields_completed selectors_count=%d masked_fields_count=%d",
        len(engine._raw_selectors),
        masked_count,
    )
    return json.dumps(redacted, ensure_ascii=False)


format_path_variants = JsonSelectorEngine.format_path_variants
_format_path_variants = format_path_variants


def _redact_node(
    node: Any,
    path: list[str],
    selectors: set[str],
    placeholder: str,
    masked_count: list[int] | None = None,
) -> Any:
    engine = JsonSelectorEngine(selectors)
    mc = masked_count if masked_count is not None else [0]
    if isinstance(path, MaskBreadcrumb):
        breadcrumb = path
    else:
        breadcrumb = MaskBreadcrumb()
        for segment in path:
            breadcrumb.push(str(segment))
    return engine._redact_node(node, breadcrumb, placeholder, mc)


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
