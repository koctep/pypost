"""Unit tests for the Qt-free collection import lifecycle policy (PYPOST-1264)."""

from __future__ import annotations

import dataclasses

import pytest

from pypost.core.collection_import_lifecycle_policy import (
    DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY,
    CollectionImportLifecyclePolicy,
    ImportTeardownDeadline,
)

pytestmark = pytest.mark.timeout(10)


class FakeClock:
    """Monotonic fake clock in seconds that moves only when advanced."""

    def __init__(self) -> None:
        self._now = 1000.0

    def __call__(self) -> float:
        return self._now

    def advance(self, ms: float) -> None:
        self._now += ms / 1000.0


def test_default_policy_values() -> None:
    policy = DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY
    assert policy == CollectionImportLifecyclePolicy()
    assert (
        policy.teardown_budget_ms,
        policy.final_join_ms,
        policy.worker_finish_join_ms,
        policy.idle_poll_ms,
        policy.budget_tolerance_ms,
    ) == (5000, 100, 100, 10, 50)


@pytest.mark.parametrize(
    ("timeout_ms", "expected"), [(None, 5000), (0, 0), (-5, 0), (300, 300)]
)
def test_resolve_budget_ms(timeout_ms: int | None, expected: int) -> None:
    assert CollectionImportLifecyclePolicy().resolve_budget_ms(timeout_ms) == expected


def test_policy_is_frozen() -> None:
    policy = CollectionImportLifecyclePolicy()
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.final_join_ms = 1  # type: ignore[misc]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"teardown_budget_ms": -1},
        {"budget_tolerance_ms": -1},
        {"idle_poll_ms": 1.5},
        {"final_join_ms": True},
        {"teardown_budget_ms": 50, "final_join_ms": 100},
        {"teardown_budget_ms": 50, "final_join_ms": 10, "worker_finish_join_ms": 60},
    ],
)
def test_policy_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        CollectionImportLifecyclePolicy(**kwargs)  # type: ignore[arg-type]


def test_deadline_remaining_bounded_and_expired() -> None:
    clock = FakeClock()
    deadline = ImportTeardownDeadline.start(300, clock=clock)
    assert deadline.budget_ms == 300
    assert deadline.remaining_ms() == 300
    assert deadline.bounded(100) == 100
    assert not deadline.expired

    clock.advance(100)
    assert deadline.elapsed_ms() == 100
    assert deadline.remaining_ms() == 200

    clock.advance(150)
    assert deadline.bounded(100) == 50

    clock.advance(500)
    assert deadline.remaining_ms() == 0
    assert deadline.bounded(100) == 0
    assert deadline.expired


def test_deadline_truncates_and_never_rounds_up() -> None:
    clock = FakeClock()
    deadline = ImportTeardownDeadline.start(50, clock=clock)
    clock.advance(0.6)
    assert deadline.remaining_ms() == 49
    assert deadline.elapsed_ms() == 0


def test_zero_budget_is_expired_immediately() -> None:
    deadline = ImportTeardownDeadline.start(0, clock=FakeClock())
    assert deadline.expired
    assert deadline.remaining_ms() == 0
    assert deadline.bounded(10) == 0
