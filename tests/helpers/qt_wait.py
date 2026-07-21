"""Bounded Qt event-loop polling helpers for tests.

Re-exports the production agent wait helper so tests do not maintain a second
poll loop (PYPOST-837 / PYPOST-840). Prefer importing from ``pypost.agent`` in
new agent-facing tests.
"""

from __future__ import annotations

from pypost.agent.ui_wait import wait_until

__all__ = ["wait_until"]
