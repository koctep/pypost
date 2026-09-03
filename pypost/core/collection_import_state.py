"""Lifecycle state for the Import Collection flow (PYPOST-1228).

Extracted so ``CollectionImportActions`` has one authoritative, named notion of
"what is this import doing right now" instead of the ad hoc ``_preparing``
boolean plus ``_worker`` presence check it used before. Qt-free, following the
``ImportConflictDecision(str, Enum)`` precedent in
``pypost.core.import_conflicts`` (string enum for readable logging/repr and
easy test assertions).
"""
from __future__ import annotations

from enum import Enum


class CollectionImportState(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    PARSING = "parsing"
    APPLYING = "applying"
