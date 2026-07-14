from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KeyRegistry:
    active_key_id: str
    keys: dict[str, str]
