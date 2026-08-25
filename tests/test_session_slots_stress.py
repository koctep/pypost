"""PYPOST-1147: high-concurrency stress benchmarks for SessionSlots.

Dedicated stress module hammering slot acquisition, ceiling contention, and
idempotent release under 50+ concurrent worker threads. Closes missing-test
debt from ai-tasks/PYPOST-1136/60-tech-debt.md.

Architecture defaults (20-architecture.md):
- STRESS_WORKER_COUNT = 64 (>= 50 concurrent threads)
- STRESS_BURST_CYCLES = 50 rapid acquire/release cycles per worker
- STRESS_MAX_SLOTS = 8 concurrent ceiling
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import threading
import time

import pytest

from pypost.core.websocket_session_policy import SessionSlots

pytestmark = pytest.mark.timeout(60)

# Architecture constants — tune here, not scattered in test bodies.
STRESS_WORKER_COUNT = 64
STRESS_BURST_CYCLES = 50
STRESS_MAX_SLOTS = 8
STRESS_COMPLETION_BUDGET_SECONDS = 30.0


@dataclass(frozen=True)
class BurstWorkerStats:
    """Per-worker outcome counters from a stress burst."""

    worker_id: int
    successful_acquires: int
    max_concurrent_refusals: int
    peak_observed_active: int


def _run_burst_worker(
    slots: SessionSlots,
    worker_id: int,
    cycles: int,
) -> BurstWorkerStats:
    """Execute rapid acquire/release cycles for one worker thread."""
    successful = 0
    local_peak = 0

    for cycle in range(cycles):
        session_id = f"stress-worker-{worker_id}-cycle-{cycle}"
        result = slots.acquire(session_id)
        active = slots.active_count
        local_peak = max(local_peak, active)

        assert result.allowed is True
        successful += 1
        assert active <= STRESS_MAX_SLOTS
        assert slots.is_holding_slot(session_id)
        assert slots.release(session_id) is True

    return BurstWorkerStats(
        worker_id=worker_id,
        successful_acquires=successful,
        max_concurrent_refusals=0,
        peak_observed_active=local_peak,
    )


def _run_all_workers(
    slots: SessionSlots,
    *,
    worker_count: int,
    cycles: int,
) -> list[BurstWorkerStats]:
    def task(worker_id: int) -> BurstWorkerStats:
        return _run_burst_worker(slots, worker_id, cycles)

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(task, range(worker_count)))


class TestSessionSlotsHighConcurrencyStress:
    """Extreme contention stress benchmarks for SessionSlots (PYPOST-1147)."""

    def test_stress_worker_count_meets_architecture_minimum(self) -> None:
        """Architecture requires >= 50 concurrent worker threads."""
        assert STRESS_WORKER_COUNT >= 50

    def test_session_slots_high_concurrency_acquire_release_burst(self) -> None:
        """64 workers × burst cycles: active_count never exceeds ceiling; no leaks."""
        slots = SessionSlots(max_slots=STRESS_MAX_SLOTS)

        stats = _run_all_workers(
            slots,
            worker_count=STRESS_WORKER_COUNT,
            cycles=STRESS_BURST_CYCLES,
        )

        assert len(stats) == STRESS_WORKER_COUNT
        assert slots.active_count == 0
        assert all(entry.peak_observed_active <= STRESS_MAX_SLOTS for entry in stats)
        total_success = sum(entry.successful_acquires for entry in stats)
        assert total_success == STRESS_WORKER_COUNT * STRESS_BURST_CYCLES
        assert max(entry.peak_observed_active for entry in stats) >= 1

    def test_session_slots_sustained_ceiling_contention(self) -> None:
        """Under full ceiling, workers observe max_concurrent refusals; slots drain cleanly."""
        slots = SessionSlots(max_slots=STRESS_MAX_SLOTS)
        hold_barrier = threading.Barrier(STRESS_MAX_SLOTS + 1)
        release_event = threading.Event()
        refusal_count = 0
        refusal_lock = threading.Lock()

        def holder(worker_id: int) -> None:
            session_id = f"holder-{worker_id}"
            result = slots.acquire(session_id)
            assert result.allowed is True
            hold_barrier.wait(timeout=5.0)
            release_event.wait(timeout=5.0)
            assert slots.release(session_id) is True

        def contender(worker_id: int) -> None:
            nonlocal refusal_count
            session_id = f"contender-{worker_id}"
            result = slots.acquire(session_id)
            if not result.allowed:
                assert result.reason == "max_concurrent"
                with refusal_lock:
                    refusal_count += 1
            else:
                slots.release(session_id)

        with ThreadPoolExecutor(max_workers=STRESS_WORKER_COUNT) as executor:
            holder_futures = [
                executor.submit(holder, worker_id)
                for worker_id in range(STRESS_MAX_SLOTS)
            ]
            hold_barrier.wait(timeout=5.0)
            assert slots.active_count == STRESS_MAX_SLOTS

            contender_futures = [
                executor.submit(contender, worker_id)
                for worker_id in range(STRESS_MAX_SLOTS, STRESS_WORKER_COUNT)
            ]

            for future in contender_futures:
                future.result(timeout=10.0)

            assert refusal_count > 0

            release_event.set()
            for future in holder_futures:
                future.result(timeout=10.0)

        assert slots.active_count == 0

    def test_session_slots_stress_completes_within_timeout(self) -> None:
        """Full burst benchmark completes within generous CI budget (non-flaky sanity)."""
        slots = SessionSlots(max_slots=STRESS_MAX_SLOTS)
        started = time.monotonic()

        _run_all_workers(
            slots,
            worker_count=STRESS_WORKER_COUNT,
            cycles=STRESS_BURST_CYCLES,
        )

        elapsed = time.monotonic() - started
        assert elapsed < STRESS_COMPLETION_BUDGET_SECONDS
        assert slots.active_count == 0
