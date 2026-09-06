"""Plain text -> Atlassian Document Format (ADF) v1 conversion (PYPOST-1283).

Jira Cloud's REST API v3 requires rich-text fields (such as an issue
description) to be submitted as ADF documents rather than plain strings. This
module provides a small, Jira-agnostic conversion so neither a GUI user nor
an MCP agent has to hand-author the nested ADF JSON structure: a request
template can simply call ``to_adf(description)`` on a plain-text value.

The function is registered as a Jinja global in
``pypost.core.function_registry`` alongside other pure template helpers
(``base64``, ``urlencode``, ``to_int``).
"""
from __future__ import annotations

import json
from typing import Any


def _paragraph(text: str) -> dict[str, Any]:
    if not text:
        return {"type": "paragraph", "content": []}
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}],
    }


def to_adf(text: str) -> str:
    """Convert plain text into a JSON-serialized ADF v1 document.

    A single line of text becomes a document with one paragraph containing
    one text node. Blank-line-separated blocks become one paragraph per
    block. An empty string produces a valid document with a single empty
    paragraph (Jira Cloud accepts this).

    Args:
        text: Plain text to convert. May be empty, single-line, or contain
            blank-line-separated paragraphs.

    Returns:
        A JSON string for the ADF document, suitable for substitution
        unquoted into a JSON request body template (e.g.
        ``"description": {{ to_adf(description) }}``).
    """
    text = text or ""
    blocks = text.split("\n\n") if text else [""]
    content = [_paragraph(block) for block in blocks]
    document = {"version": 1, "type": "doc", "content": content}
    return json.dumps(document)
