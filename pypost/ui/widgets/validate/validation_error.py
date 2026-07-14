"""Shared types for body format validation."""

from __future__ import annotations


from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    line: int
    column: int
    message: str
