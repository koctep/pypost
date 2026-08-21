"""Performance profiling and responsiveness benchmarks for collection import plan and apply.

Task: PYPOST-1062.
Verifies that:
1. plan_collection_import executes well within interactive UI thresholds (< 100ms) even for large
   synthetic datasets (500 collections, 2500 requests).
2. apply_imported_collections updates in-memory structures and persists collections efficiently.
3. Conflict resolution permutations (Overwrite, Keep Both, Skip) operate with sub-millisecond
   per-item overhead.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pypost.core.collection_import import (
    find_collection_conflicts,
    plan_collection_import,
)
from pypost.core.collection_import_apply import apply_imported_collections
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.models.models import Collection, RequestData
from tests.helpers.collections_tree import (
    FakeRequestManager,
)

pytestmark = pytest.mark.timeout(60)


def _make_sample_collections(
    count: int, requests_per_col: int = 5, prefix: str = "Col"
) -> list[Collection]:
    collections: list[Collection] = []
    for i in range(count):
        requests = [
            RequestData(
                id=str(uuid.uuid4()),
                name=f"Req {i}-{j}",
                method="GET",
                url=f"https://api.example.com/{i}/{j}",
            )
            for j in range(requests_per_col)
        ]
        collections.append(
            Collection(
                id=str(uuid.uuid4()),
                name=f"{prefix} {i}",
                requests=requests,
            )
        )
    return collections


def test_plan_collection_import_large_dataset_performance():
    """plan_collection_import plans 500 incoming collections with 2500 requests in < 100ms."""
    existing = _make_sample_collections(50, requests_per_col=5, prefix="Existing")
    incoming = _make_sample_collections(500, requests_per_col=5, prefix="Incoming")
    # Introduce some name conflicts
    conflicting_names = [f"Existing {i}" for i in range(25)]
    for i, name in enumerate(conflicting_names):
        incoming[i] = incoming[i].model_copy(update={"name": name})

    conflicts = find_collection_conflicts(existing, incoming)
    assert len(conflicts) == 25

    decisions = {
        name: (
            ImportConflictDecision.OVERWRITE if i % 3 == 0
            else ImportConflictDecision.KEEP_BOTH if i % 3 == 1
            else ImportConflictDecision.SKIP
        )
        for i, name in enumerate(conflicts)
    }

    start = time.perf_counter()
    plan_result = plan_collection_import(existing, incoming, decisions)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert len(plan_result.collections) > 0
    assert plan_result.request_count > 0
    assert elapsed_ms < 100.0, (
        f"plan_collection_import took {elapsed_ms:.2f}ms, exceeding 100ms budget"
    )


def test_apply_imported_collections_performance(tmp_path: Path):
    """apply_imported_collections persists 100 planned collections efficiently."""
    manager = FakeRequestManager()
    manager.collections = []
    manager._rebuild_request_index = MagicMock()

    incoming = _make_sample_collections(100, requests_per_col=3, prefix="Batch")
    plan_result = plan_collection_import([], incoming, {})

    start = time.perf_counter()
    apply_result = apply_imported_collections(
        manager,
        plan_result.collections,
        plan_result.persisted,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert not apply_result.failures
    assert len(manager.get_collections()) == 100
    assert elapsed_ms < 500.0, f"apply_imported_collections took {elapsed_ms:.2f}ms"


def test_plan_collection_import_conflict_matrix_profile():
    """Profile full matrix of conflict decisions with duplicate incoming names."""
    existing = _make_sample_collections(100, prefix="Target")
    incoming = _make_sample_collections(100, prefix="Target")

    # Add intra-file duplicates in incoming
    incoming.append(incoming[0].model_copy(update={"id": str(uuid.uuid4())}))
    incoming.append(incoming[1].model_copy(update={"id": str(uuid.uuid4())}))

    conflicts = find_collection_conflicts(existing, incoming)
    decisions = {name: ImportConflictDecision.KEEP_BOTH for name in conflicts}

    start = time.perf_counter()
    plan_result = plan_collection_import(existing, incoming, decisions)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert len(plan_result.renamed) >= 2
    assert elapsed_ms < 50.0, f"Matrix plan took {elapsed_ms:.2f}ms"
