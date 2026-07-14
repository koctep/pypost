"""Shared request field types for HTTP transport and history masking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RequestFields:
    """Template-resolved URL, headers, and body for an HTTP request."""

    url: str
    headers: Dict[str, str]
    body: str


# Semantic aliases — same frozen dataclass shape, different usage contexts.
ResolvedRequestFields = RequestFields
MaskedRequestData = RequestFields
