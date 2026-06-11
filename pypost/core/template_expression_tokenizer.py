"""Shared tokenization for ``{{ ... }}`` template placeholders."""

import re

_PLACEHOLDER_INNER_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")


def tokenize_template_expressions(content: str) -> list[str]:
    """
    Return inner expression text for each ``{{ ... }}`` placeholder in ``content``.

    Matches the legacy ``re.findall(r"\\{\\{\\s*(.*?)\\s*\\}\\}", content)`` contract:
    non-greedy inner capture with optional surrounding whitespace inside delimiters.
    """
    return _PLACEHOLDER_INNER_PATTERN.findall(content)
