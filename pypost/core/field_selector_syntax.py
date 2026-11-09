"""Field selector syntax validation for Hidden Fields (PYPOST-1387).

Validates user-authored selectors against the documented supported vocabulary
(simple key, dotted path, array wildcard, header selector). Pure / no Qt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pypost.core.header_selector_prefix import header_selector_name

__all__ = ["FieldSelectorSyntaxResult", "validate_field_selector"]

_BRACKET_WILDCARD_RE = re.compile(r"\[\*\]")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

_SUGGESTIONS = (
    "Supported forms: simple key (token), dotted path (auth.token), "
    "array wildcard (users[*].email or [*].id), "
    "header selector (header:Authorization)."
)

_UNSUPPORTED_MESSAGE = (
    "Unsupported or invalid field selector syntax. "
    "This expression is not accepted by response masking."
)


@dataclass(frozen=True)
class FieldSelectorSyntaxResult:
    """Outcome of checking one field selector string."""

    ok: bool
    is_empty: bool
    message: str
    suggestions: str


def _ok(*, is_empty: bool = False) -> FieldSelectorSyntaxResult:
    return FieldSelectorSyntaxResult(
        ok=True,
        is_empty=is_empty,
        message="",
        suggestions="",
    )


def _invalid(message: str, suggestions: str = _SUGGESTIONS) -> FieldSelectorSyntaxResult:
    return FieldSelectorSyntaxResult(
        ok=False,
        is_empty=False,
        message=message,
        suggestions=suggestions,
    )


def _normalize_wildcards(text: str) -> str:
    """Normalize ``[*]`` surface form to dotted ``*`` segments."""
    return _BRACKET_WILDCARD_RE.sub(".*.", text)


def _is_valid_segment(segment: str) -> bool:
    return segment == "*" or bool(_IDENTIFIER_RE.match(segment))


def _validate_path(text: str) -> FieldSelectorSyntaxResult:
    if " " in text or "\t" in text:
        return _invalid(_UNSUPPORTED_MESSAGE)
    if "$" in text or "?" in text or "(" in text or ")" in text:
        return _invalid(_UNSUPPORTED_MESSAGE)
    if text.startswith(".") or text.endswith("."):
        return _invalid(_UNSUPPORTED_MESSAGE)
    if ".." in text:
        return _invalid(_UNSUPPORTED_MESSAGE)

    # Reject any remaining brackets that are not the [*] wildcard (already normalized).
    if "[" in text or "]" in text:
        return _invalid(_UNSUPPORTED_MESSAGE)

    segments = text.split(".")
    if not segments or any(segment == "" for segment in segments):
        return _invalid(_UNSUPPORTED_MESSAGE)
    if not all(_is_valid_segment(segment) for segment in segments):
        return _invalid(_UNSUPPORTED_MESSAGE)
    return _ok()


def validate_field_selector(text: str) -> FieldSelectorSyntaxResult:
    """Return syntax evaluation for one selector string (strip-aware)."""
    cleaned = text.strip()
    if not cleaned:
        return _ok(is_empty=True)

    name = header_selector_name(cleaned)
    if name is not None:
        if not name.strip():
            return _invalid(
                "Header selector requires a non-empty name after 'header:'. "
                "This form is not accepted.",
                suggestions="Example: header:Authorization",
            )
        return _ok()

    if "." not in cleaned and "[" not in cleaned and "]" not in cleaned:
        if "$" in cleaned or " " in cleaned or "\t" in cleaned:
            return _invalid(_UNSUPPORTED_MESSAGE)
        if not _IDENTIFIER_RE.match(cleaned):
            return _invalid(_UNSUPPORTED_MESSAGE)
        return _ok()

    # A written ".." is an empty step. Reject it before collapse turns it into ".".
    if ".." in cleaned:
        return _invalid(_UNSUPPORTED_MESSAGE)

    normalized = _normalize_wildcards(cleaned)
    # Collapse accidental double dots from adjacent [*] replacements / leading [*]
    while ".." in normalized:
        normalized = normalized.replace("..", ".")
    normalized = normalized.strip(".")
    return _validate_path(normalized)
