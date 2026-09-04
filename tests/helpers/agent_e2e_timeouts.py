"""Shared timeout policies for agent e2e scenarios (PYPOST-983)."""

from __future__ import annotations

# Near-zero budget used by forced timeout companions to exercise diagnostics.
FORCED_SETTLE_TIMEOUT_S = 0.05

__all__ = ["FORCED_SETTLE_TIMEOUT_S"]
