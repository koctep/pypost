"""Shared types for code folding."""

from __future__ import annotations


from dataclasses import dataclass
from enum import Enum


class BodyFormat(Enum):
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    PLAIN = "plain"


@dataclass(frozen=True)
class FoldRegion:
    region_id: str
    header_block: int
    start_block: int
    end_block: int
    kind: str
