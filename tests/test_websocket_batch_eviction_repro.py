"""Reproduction tests for MessageStream batch eviction API (PYPOST-1141).

Covers:
1. Public calculate_batch_evictions API on MessageStream.
2. Capacity and memory-budget FIFO eviction planning.
3. apply_batch_evictions atomic mutation.
4. StreamListModel architectural decoupling from private MessageStream members.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from pypost.core.websocket_stream import BatchEvictionPlan, MessageStream, StreamEntry

pytestmark = pytest.mark.timeout(30)


def _create_sample_entry(
    seq: int = 1,
    payload: str = '{"status":"ok"}',
) -> StreamEntry:
    return StreamEntry(
        seq=seq,
        ts_utc="2026-08-22T12:00:00.000Z",
        kind="message",
        direction="in",
        payload_format="json",
        payload=payload,
        byte_size=len(payload.encode("utf-8")),
    )


class TestMessageStreamBatchEvictionApi:
    """Headless tests for MessageStream.calculate_batch_evictions (PYPOST-1141)."""

    @pytest.mark.timeout(30)
    def test_message_stream_has_calculate_batch_evictions(self) -> None:
        """MessageStream exposes calculate_batch_evictions as a public method."""
        stream = MessageStream()
        assert callable(getattr(stream, "calculate_batch_evictions", None))

    @pytest.mark.timeout(30)
    def test_calculate_batch_evictions_empty_batch(self) -> None:
        """Empty batch returns a zero-eviction plan."""
        stream = MessageStream(max_entries=3)
        stream.append(_create_sample_entry(seq=1))

        plan = stream.calculate_batch_evictions([])

        assert plan == BatchEvictionPlan(0, 0, 0, 0, ())

    @pytest.mark.timeout(30)
    def test_calculate_batch_evictions_capacity(self) -> None:
        """Capacity eviction plan evicts oldest existing rows before appending."""
        stream = MessageStream(max_entries=3)
        for seq in range(1, 4):
            stream.append(_create_sample_entry(seq=seq, payload=f"msg {seq}"))

        plan = stream.calculate_batch_evictions(
            [_create_sample_entry(seq=4, payload="msg 4"),
             _create_sample_entry(seq=5, payload="msg 5")]
        )

        assert plan.existing_evicted == 2
        assert plan.dropped_capacity == 2
        assert plan.dropped_memory_budget == 0
        assert plan.total_evicted == 2
        assert [e.seq for e in plan.entries_to_append] == [4, 5]

    @pytest.mark.timeout(30)
    def test_calculate_batch_evictions_memory_budget(self) -> None:
        """Memory-budget eviction plan reports memory_budget drop cause."""
        stream = MessageStream(max_entries=100, memory_budget_bytes=60)
        stream.append(_create_sample_entry(seq=1, payload="A" * 30))
        stream.append(_create_sample_entry(seq=2, payload="B" * 25))

        plan = stream.calculate_batch_evictions(
            [_create_sample_entry(seq=3, payload="C" * 40)]
        )

        assert plan.dropped_memory_budget >= 1
        assert plan.total_evicted >= 1
        assert plan.entries_to_append

    @pytest.mark.timeout(30)
    def test_apply_batch_evictions_mutates_stream(self) -> None:
        """apply_batch_evictions applies plan atomically to the buffer."""
        stream = MessageStream(max_entries=3)
        for seq in range(1, 4):
            stream.append(_create_sample_entry(seq=seq, payload=f"msg {seq}"))

        plan = stream.calculate_batch_evictions(
            [_create_sample_entry(seq=4, payload="msg 4"),
             _create_sample_entry(seq=5, payload="msg 5")]
        )
        stream.apply_batch_evictions(plan)

        assert len(stream) == 3
        assert [e.seq for e in stream.snapshot()] == [3, 4, 5]
        assert stream.dropped == {"capacity": 2, "memory_budget": 0}


class TestStreamListModelDecoupling:
    """Architectural tests ensuring StreamListModel uses public MessageStream APIs."""

    @pytest.mark.timeout(30)
    def test_stream_list_model_no_private_member_access(self) -> None:
        """StreamListModel must not access MessageStream._entries or _retained_bytes."""
        model_file = (
            Path(__file__).resolve().parents[1]
            / "pypost"
            / "ui"
            / "widgets"
            / "websocket"
            / "stream_model.py"
        )
        tree = ast.parse(model_file.read_text(encoding="utf-8"), filename=str(model_file))
        forbidden: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in ("_entries", "_retained_bytes"):
                forbidden.append(node.attr)

        assert not forbidden, (
            f"stream_model.py accesses forbidden MessageStream private members: {forbidden}"
        )
