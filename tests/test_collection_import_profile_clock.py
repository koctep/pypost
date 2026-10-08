"""PYPOST-1263: distinguish planner CPU work from external scheduling delay."""

from __future__ import annotations

import pytest

from pypost.core.collection_import import CollectionImportPlanResult
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.models.models import Collection
import tests.test_collection_import_profile as profile

pytestmark = pytest.mark.timeout(10)


class _ObservedClocks:
    def __init__(self, cpu_seconds: float, wall_seconds: float, events: list[str]) -> None:
        self.cpu_seconds = cpu_seconds
        self.wall_seconds = wall_seconds
        self.events = events
        self.wall_reads = 0
        self.cpu_reads = 0

    def perf_counter(self) -> float:
        self.events.append("wall")
        self.wall_reads += 1
        assert self.wall_reads <= 2, "Benchmark must measure a single wall interval"
        return 0.0 if self.wall_reads == 1 else self.wall_seconds

    def thread_time(self) -> float:
        self.events.append("cpu")
        self.cpu_reads += 1
        assert self.cpu_reads <= 2, "Benchmark must measure a single thread CPU interval"
        return 0.0 if self.cpu_reads == 1 else self.cpu_seconds


@pytest.mark.parametrize(
    ("cpu_seconds", "wall_seconds", "reject"),
    [
        pytest.param(0.02, 0.5, False, id="external-descheduling"),
        pytest.param(0.15, 0.5, True, id="excess-planner-work"),
        pytest.param(0.1, 0.5, True, id="strict-cpu-boundary"),
        # Synthetic policy probe: independent clock values, not a physical CPU measurement.
        pytest.param(0.15, 0.01, True, id="synthetic-low-wall-high-cpu"),
    ],
)
def test_planner_benchmark_distinguishes_cpu_work_from_wall_delay(
    monkeypatch: pytest.MonkeyPatch, cpu_seconds: float, wall_seconds: float, reject: bool
) -> None:
    events: list[str] = []
    clocks = _ObservedClocks(cpu_seconds, wall_seconds, events)
    real_planner = profile.plan_collection_import
    real_make_collections = profile._make_sample_collections
    real_find_conflicts = profile.find_collection_conflicts
    planner_calls = 0

    def observe_make_collections(
        count: int, requests_per_col: int = 5, prefix: str = "Col"
    ) -> list[Collection]:
        result = real_make_collections(count, requests_per_col, prefix)
        events.append("fixture-done")
        return result

    def observe_find_conflicts(
        existing: list[Collection], incoming: list[Collection]
    ) -> list[str]:
        result = real_find_conflicts(existing, incoming)
        events.append("conflicts-done")
        return result

    def observe_planner(
        existing: list[Collection],
        incoming: list[Collection],
        decisions: dict[str, ImportConflictDecision],
    ) -> CollectionImportPlanResult:
        nonlocal planner_calls
        planner_calls += 1
        events.append("planner-start")
        assert len(existing) == 50
        assert len(incoming) == 500
        assert sum(len(collection.requests) for collection in incoming) == 2500
        conflicts = real_find_conflicts(existing, incoming)
        assert len(conflicts) == 25
        assert set(decisions) == set(conflicts)
        assert set(decisions.values()) == {
            ImportConflictDecision.OVERWRITE,
            ImportConflictDecision.KEEP_BOTH,
            ImportConflictDecision.SKIP,
        }
        result = real_planner(existing, incoming, decisions)
        events.append("planner-end")
        return result

    monkeypatch.setattr(profile, "time", clocks)
    monkeypatch.setattr(profile, "plan_collection_import", observe_planner)
    monkeypatch.setattr(profile, "_make_sample_collections", observe_make_collections)
    monkeypatch.setattr(profile, "find_collection_conflicts", observe_find_conflicts)

    if reject:
        with pytest.raises(AssertionError, match=r"(?i)CPU") as failure:
            profile.test_plan_collection_import_large_dataset_performance()
        message = str(failure.value)
        assert "100" in message and str(round(wall_seconds * 1000)) in message
        assert "wall" in message.lower()
        assert str(round(cpu_seconds * 1000)) in message
    else:
        profile.test_plan_collection_import_large_dataset_performance()

    assert planner_calls == 1
    assert clocks.cpu_reads == clocks.wall_reads == 2
    assert events.count("fixture-done") == 2
    assert events.count("conflicts-done") == 1
    for clock in ("cpu", "wall"):
        positions = [index for index, event in enumerate(events) if event == clock]
        assert max(index for index, event in enumerate(events) if event == "fixture-done") < (
            positions[0]
        )
        assert events.index("conflicts-done") < positions[0]
        assert positions[0] < events.index("planner-start")
        assert positions[1] > events.index("planner-end")
