"""Dynamic template resolution and secrets sanitization for MCP proxy headers."""
from __future__ import annotations

import re
from typing import Iterable, Mapping

from pypost.core.sensitive_text_sanitizer import (
    HIDDEN_PLACEHOLDER,
    _SENSITIVE_HEADER_NAMES,
    sanitize_text,
)
from pypost.core.template_expression_tokenizer import (
    TEMPLATE_PLACEHOLDER_PATTERN,
    tokenize_template_expressions,
)
from pypost.core.template_service import TemplateService


class McpUnresolvedVariableError(Exception):
    """Raised when a proxy header references an undefined environment variable."""

    def __init__(
        self,
        variable_name: str,
        header_name: str | None = None,
        message: str | None = None,
    ) -> None:
        self.variable_name = variable_name
        self.header_name = header_name
        if message is None:
            if header_name:
                message = (
                    f"Missing environment variable: '{variable_name}' "
                    f"referenced in header '{header_name}'"
                )
            else:
                message = f"Missing environment variable: '{variable_name}'"
        super().__init__(message)


def resolve_proxy_headers(
    headers: Mapping[str, str],
    env_vars: Mapping[str, str],
    template_service: TemplateService | None = None,
) -> dict[str, str]:
    """Resolve dynamic template placeholders (e.g. {{ VAR }}) in proxy headers.

    Raises:
        McpUnresolvedVariableError: If any template variable is missing from env_vars.
    """
    resolved: dict[str, str] = {}
    for header_name, header_value in headers.items():
        if not header_value:
            resolved[header_name] = header_value
            continue

        placeholders = tokenize_template_expressions(header_value)
        for placeholder in placeholders:
            var_name = placeholder.strip()
            if var_name not in env_vars:
                raise McpUnresolvedVariableError(
                    var_name,
                    header_name,
                    f"Missing environment variable: '{var_name}' in header '{header_name}'",
                )

        if template_service is not None:
            resolved[header_name] = template_service.render_string(
                header_value, dict(env_vars)
            )
        else:
            def _substitute(match: re.Match) -> str:
                name = match.group(1).strip()
                return str(env_vars.get(name, match.group(0)))

            resolved[header_name] = TEMPLATE_PLACEHOLDER_PATTERN.sub(
                _substitute, header_value
            )

    return resolved


def sanitize_proxy_headers(
    headers: Mapping[str, str],
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> dict[str, str]:
    """Sanitize proxy headers by redacting sensitive keys and hidden values."""
    result: dict[str, str] = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower == "authorization":
            if value.strip().lower().startswith("bearer "):
                result[key] = f"Bearer {HIDDEN_PLACEHOLDER}"
            else:
                result[key] = HIDDEN_PLACEHOLDER
        elif key_lower in _SENSITIVE_HEADER_NAMES:
            result[key] = HIDDEN_PLACEHOLDER
        else:
            result[key] = sanitize_text(
                value, env_vars=env_vars, hidden_keys=hidden_keys
            )
    return result
