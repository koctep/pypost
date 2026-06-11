"""Shared tokenization for ``{{ ... }}`` template placeholders."""

import re

TEMPLATE_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")


def tokenize_template_expressions(content: str) -> list[str]:
    """
    Return inner expression text for each ``{{ ... }}`` placeholder in ``content``.

    Matches the legacy ``re.findall(r"\\{\\{\\s*(.*?)\\s*\\}\\}", content)`` contract:
    non-greedy inner capture with optional surrounding whitespace inside delimiters.
    """
    return TEMPLATE_PLACEHOLDER_PATTERN.findall(content)
