"""Conflict primitives shared by the environment and collection import flows.

Extracted from ``pypost.core.environment_import`` (PYPOST-986) so the collection
import flow (PYPOST-987) can reuse the same three-way decision and the same
``Copy of X`` disambiguation without duplicating either. Both remain importable
from ``pypost.core.environment_import`` for existing callers.
"""
from __future__ import annotations

from enum import Enum

from pypost.core.environment_messages import format_copy_of_name


class ImportConflictDecision(str, Enum):
    OVERWRITE = "overwrite"
    KEEP_BOTH = "keep_both"
    SKIP = "skip"


def generate_import_copy_name(name: str, existing_names: set[str]) -> str:
    """"Copy of X" when free, else "Copy of X (2)", "(3)", ... until unique."""
    candidate = format_copy_of_name(name)
    if candidate not in existing_names:
        return candidate
    suffix = 2
    while f"{candidate} ({suffix})" in existing_names:
        suffix += 1
    return f"{candidate} ({suffix})"
