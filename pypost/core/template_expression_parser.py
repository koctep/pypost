"""Lexer and small grammar helpers for ``{{ ... }}`` expressions."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressionToken:
    """A template expression and its source span."""

    expression: str
    start: int
    end: int
    closed: bool


_CALL_RE = re.compile(r"(?<!\.)\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
_IDENTIFIER_RE = re.compile(r"(?<!\.)\b([a-zA-Z_][a-zA-Z0-9_]*)\b")


def lex_template_expressions(content: str) -> tuple[ExpressionToken, ...]:
    """Return closed and unclosed template expressions in one delimiter scan."""
    tokens: list[ExpressionToken] = []
    cursor = 0
    while True:
        start = content.find("{{", cursor)
        if start < 0:
            return tuple(tokens)
        close = content.find("}}", start + 2)
        next_open = content.find("{{", start + 2)
        if close < 0 or (next_open >= 0 and next_open < close):
            end = next_open if next_open >= 0 else len(content)
            tokens.append(ExpressionToken(content[start + 2:end].strip(), start, end, False))
            cursor = end
            continue
        end = close + 2
        tokens.append(ExpressionToken(content[start + 2:close].strip(), start, end, True))
        cursor = end


def function_names(expression: str) -> tuple[str, ...]:
    """Return function names in an expression, including nested calls."""
    return tuple(match.group(1) for match in _CALL_RE.finditer(expression))


def identifier_names(expression: str) -> tuple[str, ...]:
    """Return identifier names that are not object-path segments."""
    return tuple(match.group(1) for match in _IDENTIFIER_RE.finditer(expression))


def split_single_argument(arguments: str) -> str | None:
    """Return one top-level argument, respecting nested calls and quoted strings."""
    depth = 0
    quote: str | None = None
    escaped = False
    for char in arguments:
        if escaped:
            escaped = False
        elif char == "\\" and quote is not None:
            escaped = True
        elif quote is not None:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            return None
    return arguments.strip() if depth == 0 and quote is None else None
