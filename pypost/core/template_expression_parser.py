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


@dataclass(frozen=True)
class ArgumentParseResult:
    """Outcome of parsing a function argument string."""

    argument: str | None
    has_multiple_arguments: bool
    is_malformed: bool


def split_single_argument(arguments: str) -> str | None:
    """Return one top-level argument, respecting nested calls and quoted strings."""
    return parse_function_argument(arguments).argument


def parse_function_argument(raw_arg: str) -> ArgumentParseResult:
    """Parse an argument string, distinguishing arity violations from syntax malformations.

    Args:
        raw_arg: Raw text within outer function parentheses.

    Returns:
        ArgumentParseResult indicating:
        - argument: The single argument string if well-formed or extractable, else None.
        - has_multiple_arguments: True if top-level comma encountered at depth 0.
        - is_malformed: True if parentheses or quotes are unbalanced.
    """
    depth = 0
    quote: str | None = None
    escaped = False
    has_multiple_arguments = False
    had_negative_depth = False

    for char in raw_arg:
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
            if depth < 0:
                had_negative_depth = True
        elif char == "," and depth == 0 and not had_negative_depth:
            has_multiple_arguments = True

    is_malformed = depth != 0 or quote is not None or had_negative_depth
    if has_multiple_arguments:
        return ArgumentParseResult(
            argument=None,
            has_multiple_arguments=True,
            is_malformed=is_malformed,
        )

    if is_malformed:
        return ArgumentParseResult(
            argument=None,
            has_multiple_arguments=False,
            is_malformed=True,
        )

    return ArgumentParseResult(
        argument=raw_arg.strip(),
        has_multiple_arguments=False,
        is_malformed=False,
    )
