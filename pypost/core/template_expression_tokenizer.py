"""Shared tokenization for ``{{ ... }}`` template placeholders."""

import re

TEMPLATE_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")

# Plain ``{{name}}`` tokens without inner whitespace — fast hover lookup (PYPOST-113).
# Capture allows digit-leading names; ``FunctionExpressionResolver`` uses stricter rules.
PLAIN_VARIABLE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")


def tokenize_template_expressions(content: str) -> list[str]:
    """
    Return inner expression text for each ``{{ ... }}`` placeholder in ``content``.

    Matches the legacy ``re.findall(r"\\{\\{\\s*(.*?)\\s*\\}\\}", content)`` contract:
    non-greedy inner capture with optional surrounding whitespace inside delimiters.
    """
    return TEMPLATE_PLACEHOLDER_PATTERN.findall(content)


def is_plain_variable_token(token: str) -> bool:
    """Return True when ``token`` is exactly ``{{name}}`` with no inner whitespace."""
    return PLAIN_VARIABLE_PATTERN.fullmatch(token) is not None


def extract_plain_variable_name(token: str) -> str | None:
    """Return the variable name from a plain ``{{name}}`` token, or None."""
    match = PLAIN_VARIABLE_PATTERN.fullmatch(token)
    return match.group(1) if match else None
