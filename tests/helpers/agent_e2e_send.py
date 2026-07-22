"""Shared Send settle timing for agent e2e scenarios (PYPOST-895)."""

from __future__ import annotations

# Wall-clock budget for wait_for_snapshot after Send in agent e2e flows.
SEND_SETTLE_TIMEOUT_S = 15.0

__all__ = ["SEND_SETTLE_TIMEOUT_S"]
