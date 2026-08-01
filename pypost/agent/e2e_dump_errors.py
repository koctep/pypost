"""Shared best-effort exception types for agent e2e failure dumps (PYPOST-960).

Used by the lifecycle dump-hook wrapper and the fixtures dump helper so
members stay aligned without circular imports between those modules.
Unexpected ``Exception`` subclasses propagate so dump bugs remain visible.
"""

DUMP_BEST_EFFORT_ERRORS = (
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
    AttributeError,
)
