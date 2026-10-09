"""Qt-free lifecycle limits for collection import wait and teardown (PYPOST-1264).

One named policy holds every time limit the collection import actions use, and
``ImportTeardownDeadline`` lets the sequential teardown phases share a single
monotonic caller budget so their waits can never add up to more than it.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, fields

Clock = Callable[[], float]


@dataclass(frozen=True)
class CollectionImportLifecyclePolicy:
    """Immutable time limits (milliseconds) for collection import lifecycle.

    Attributes:
        teardown_budget_ms: Default overall caller budget for ``wait_idle`` and
            ``teardown`` when the caller passes none.
        final_join_ms: Upper bound for the file-worker join after its signals are
            disconnected in teardown; always capped by the remaining budget.
        worker_finish_join_ms: Join after a normal ``QThread.finished``
            (PYPOST-829 H3); runs on the GUI thread, so it stays small.
        idle_poll_ms: ``wait_idle`` poll slice when no ``QApplication`` exists;
            capped by the remaining budget.
        budget_tolerance_ms: Documented allowed overrun of teardown wall time beyond
            the caller budget on an unloaded machine. A contract value, not a wait
            and not a CI timing gate.
    """

    teardown_budget_ms: int = 5000
    final_join_ms: int = 100
    worker_finish_join_ms: int = 100
    idle_poll_ms: int = 10
    budget_tolerance_ms: int = 50

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(
                    f"{field.name} must be a non-negative int, got {value!r}"
                )
        for name in ("final_join_ms", "worker_finish_join_ms", "idle_poll_ms"):
            if getattr(self, name) > self.teardown_budget_ms:
                raise ValueError(
                    f"{name} must not exceed teardown_budget_ms "
                    f"({self.teardown_budget_ms})"
                )

    def resolve_budget_ms(self, timeout_ms: int | None) -> int:
        """Return the caller budget: ``None`` → policy default, negative → 0."""
        if timeout_ms is None:
            return self.teardown_budget_ms
        return max(0, int(timeout_ms))


DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY = CollectionImportLifecyclePolicy()


class ImportTeardownDeadline:
    """One monotonic deadline that the sequential teardown phases share."""

    def __init__(self, budget_ms: int, started_s: float, clock: Clock) -> None:
        self._budget_ms = max(0, budget_ms)
        self._started_s = started_s
        self._clock = clock

    @classmethod
    def start(
        cls, budget_ms: int, clock: Clock = time.monotonic
    ) -> ImportTeardownDeadline:
        """Start a deadline of ``budget_ms`` milliseconds from ``clock()`` now."""
        return cls(budget_ms, clock(), clock)

    @property
    def budget_ms(self) -> int:
        """The caller budget this deadline was started with."""
        return self._budget_ms

    def _elapsed_us(self) -> int:
        # Whole microseconds: absorbs float noise of ``clock()`` differences (for
        # example 1000.1 - 1000.0) before truncating to milliseconds below.
        return max(0, round((self._clock() - self._started_s) * 1_000_000))

    def elapsed_ms(self) -> int:
        """Whole milliseconds elapsed since start (truncated, never negative)."""
        return self._elapsed_us() // 1000

    def remaining_ms(self) -> int:
        """Whole milliseconds left (truncated, never rounded up, never negative)."""
        return max(0, (self._budget_ms * 1000 - self._elapsed_us()) // 1000)

    def bounded(self, limit_ms: int) -> int:
        """Return ``min(limit_ms, remaining_ms())``."""
        return min(max(0, limit_ms), self.remaining_ms())

    @property
    def expired(self) -> bool:
        """True once no whole millisecond of the budget is left."""
        return self.remaining_ms() <= 0
