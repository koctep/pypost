"""One header-selector prefix, read again on every recognition call."""

from __future__ import annotations

__all__ = ["HEADER_SELECTOR_PREFIX", "header_selector_name"]

HEADER_SELECTOR_PREFIX: str = "header:"


def header_selector_name(text: str) -> str | None:
    """Return the unstripped remainder after the prefix, or None if it does not match."""
    # Re-read the module global on each call so a patch of this name is visible.
    prefix = HEADER_SELECTOR_PREFIX
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):]
    return None
