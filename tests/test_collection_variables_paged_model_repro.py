"""Failing repro for PYPOST-1427 paged CollectionVariablesTableModel virtualization.

Asserts extreme catalogs (50k vars) load instantly without eager full-record
materialization, keep a bounded chunk cache after sparse access, and preserve
selection / summary correctness across eviction.
"""

from __future__ import annotations

import time
from typing import Any

from PySide6.QtCore import Qt
import pytest

from pypost.core.collection_variable_import import ConflictStrategy
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment
from pypost.ui.models.collection_variables_table_model import (
    COL_NAME,
    COL_SELECT,
    COL_STRATEGY,
    CollectionVariablesTableModel,
)

pytestmark = [pytest.mark.timeout(60)]

EXTREME_N = 50_000
LOAD_BUDGET_S = 0.100


def _build_extreme_catalog(n: int = EXTREME_N) -> tuple[Environment, Collection]:
    """Build env + collection with n variables and ~10% collisions."""
    collision_count = n // 10
    env_vars = {f"var_{i}": f"env_{i}" for i in range(collision_count)}
    env = Environment(name="ExtremeEnv", variables=env_vars, hidden_keys=set())
    col_vars = [
        CollectionVariable(
            name=f"var_{i}",
            type="string",
            default=f"col_{i}",
            description=f"d{i}",
        )
        for i in range(n)
    ]
    collection = Collection(name="ExtremeCollection", variables=col_vars)
    return env, collection


def _cached_count(model: CollectionVariablesTableModel) -> int:
    """Return materialized row-record count (paged API or legacy dense list)."""
    cached = getattr(model, "cached_record_count", None)
    if callable(cached):
        return int(cached())
    if isinstance(cached, int):
        return cached
    records = getattr(model, "_records", None)
    if records is not None:
        return len(records)
    raise AssertionError(
        "Model must expose cached_record_count or legacy _records for cache sizing"
    )


def _chunk_budget(model: CollectionVariablesTableModel) -> int:
    chunk = int(getattr(model, "CHUNK_SIZE", 256))
    max_chunks = int(getattr(model, "MAX_CACHED_CHUNKS", 8))
    return chunk * max_chunks


@pytest.mark.timeout(60)
def test_extreme_catalog_load_is_instant_without_eager_records(qapp: Any) -> None:
    """load_collection must not eagerly allocate N row records (instant load)."""
    env, collection = _build_extreme_catalog()
    model = CollectionVariablesTableModel(env)

    started = time.perf_counter()
    model.load_collection(collection)
    elapsed = time.perf_counter() - started

    assert model.rowCount() == EXTREME_N
    assert elapsed < LOAD_BUDGET_S, (
        f"load_collection took {elapsed:.3f}s for {EXTREME_N} vars; "
        f"budget is {LOAD_BUDGET_S:.3f}s (eager full materialization)"
    )
    assert _cached_count(model) == 0, (
        "After load and before row access, materialized cache must be empty "
        f"(got {_cached_count(model)})"
    )


@pytest.mark.timeout(60)
def test_chunk_cache_stays_bounded_after_sparse_scroll(qapp: Any) -> None:
    """Touching many distant rows must not retain more than the chunk budget."""
    env, collection = _build_extreme_catalog()
    model = CollectionVariablesTableModel(env)
    model.load_collection(collection)

    budget = _chunk_budget(model)
    chunk = int(getattr(model, "CHUNK_SIZE", 256))
    # Visit enough distinct chunks to exceed the cache cap.
    visit_rows = list(range(0, EXTREME_N, chunk))[:32]
    visit_rows.extend([EXTREME_N // 2, EXTREME_N - 1])

    for row in visit_rows:
        idx = model.index(row, COL_NAME)
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == f"var_{row}"

    assert _cached_count(model) <= budget, (
        f"cached_record_count={_cached_count(model)} exceeds budget={budget}"
    )


@pytest.mark.timeout(60)
def test_selection_and_summary_survive_chunk_eviction(qapp: Any) -> None:
    """Sparse selection/strategy must survive eviction and feed summaries."""
    env, collection = _build_extreme_catalog()
    model = CollectionVariablesTableModel(env)
    model.load_collection(collection)

    chunk = int(getattr(model, "CHUNK_SIZE", 256))
    max_chunks = int(getattr(model, "MAX_CACHED_CHUNKS", 8))

    # Deselect first row and set overwrite on a colliding mid row.
    model.set_row_selected(0, False)
    mid = chunk * (max_chunks + 2)
    assert mid < EXTREME_N
    # mid is within collision range only if mid < n/10; pick a guaranteed collision.
    collide_row = 5
    model.set_row_strategy(collide_row, ConflictStrategy.OVERWRITE)

    # Force eviction of early chunks by reading far ahead.
    for row in range(0, EXTREME_N, chunk):
        if row // chunk >= max_chunks + 4:
            break
        model.data(model.index(row, COL_NAME), Qt.ItemDataRole.DisplayRole)

    # Re-read early rows (may rematerialize) — decisions must persist.
    assert model.data(
        model.index(0, COL_SELECT), Qt.ItemDataRole.CheckStateRole
    ) == Qt.CheckState.Unchecked
    assert model.get_strategy(collide_row) == ConflictStrategy.OVERWRITE
    assert "var_0" not in model.get_selected_keys()
    assert model.get_conflict_strategies().get("var_5") == ConflictStrategy.OVERWRITE

    will_add, will_overwrite, will_keep = model.get_summary_counts()
    collision_count = EXTREME_N // 10
    # All selected by default except var_0; collisions default SKIP except var_5.
    # var_0 (deselected collision) and var_5 (overwrite) are excluded from will_keep.
    assert will_overwrite == 1
    assert will_keep == collision_count - 2
    # New rows: total - collisions; var_0 is a collision so deselect doesn't change adds.
    assert will_add == EXTREME_N - collision_count


@pytest.mark.timeout(30)
def test_small_catalog_parity_unchanged(qapp: Any) -> None:
    """Small catalogs keep familiar rowCount / data / bulk strategy behavior."""
    env = Environment(
        name="Small",
        variables={"a": "1"},
        hidden_keys=set(),
    )
    collection = Collection(
        name="SmallCol",
        variables=[
            CollectionVariable(name="a", type="string", default="2"),
            CollectionVariable(name="b", type="string", default="3"),
        ],
    )
    model = CollectionVariablesTableModel(env)
    model.load_collection(collection)
    assert model.rowCount() == 2
    assert model.data(model.index(0, COL_NAME), Qt.ItemDataRole.DisplayRole) == "a"
    assert model.data(model.index(1, COL_NAME), Qt.ItemDataRole.DisplayRole) == "b"
    assert model.set_all_collision_strategy(ConflictStrategy.OVERWRITE) == 1
    assert model.get_strategy(0) == ConflictStrategy.OVERWRITE
    assert model.data(
        model.index(0, COL_STRATEGY), Qt.ItemDataRole.DisplayRole
    ) == "Overwrite"
