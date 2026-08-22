"""Virtualized Qt list model for high-frequency WebSocket message stream (PYPOST-1130).

Provides QAbstractListModel interface over bounded MessageStream ring buffer
with synchronized row insertion and FIFO eviction signals.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)

from pypost.core.websocket_stream import MessageStream, StreamEntry

logger = logging.getLogger(__name__)

__all__ = ["StreamListModel"]


class StreamListModel(QAbstractListModel):
    """Virtualized list model representing WebSocket stream entries."""

    SeqRole = int(Qt.ItemDataRole.UserRole) + 1
    TimestampRole = int(Qt.ItemDataRole.UserRole) + 2
    KindRole = int(Qt.ItemDataRole.UserRole) + 3
    DirectionRole = int(Qt.ItemDataRole.UserRole) + 4
    FormatRole = int(Qt.ItemDataRole.UserRole) + 5
    TruncatedRole = int(Qt.ItemDataRole.UserRole) + 6
    ByteSizeRole = int(Qt.ItemDataRole.UserRole) + 7
    DetailRole = int(Qt.ItemDataRole.UserRole) + 8
    StreamEntryRole = int(Qt.ItemDataRole.UserRole) + 9

    def __init__(
        self,
        stream: MessageStream | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._stream = stream if stream is not None else MessageStream()

    @property
    def stream(self) -> MessageStream:
        """Return the underlying MessageStream instance."""
        return self._stream

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        """Return number of retained entries in the model."""
        if parent.isValid():
            return 0
        return len(self._stream)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        """Return data for given index and role."""
        if not index.isValid() or not (0 <= index.row() < len(self._stream)):
            return None

        entry = self._stream[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return entry.payload
        if role == self.SeqRole:
            return entry.seq
        if role == self.TimestampRole:
            return entry.ts_utc
        if role == self.KindRole:
            return entry.kind
        if role == self.DirectionRole:
            return entry.direction
        if role == self.FormatRole:
            return entry.payload_format
        if role == self.TruncatedRole:
            return entry.truncated
        if role == self.ByteSizeRole:
            return entry.byte_size
        if role == self.DetailRole:
            return entry.detail
        if role == self.StreamEntryRole:
            return entry
        return None

    def _calculate_batch_evictions(
        self,
        batch: Sequence[StreamEntry],
    ) -> tuple[int, int, int]:
        """Simulate batch insertion to determine eviction counts.

        Returns:
            (total_evicted, dropped_capacity_count, dropped_memory_budget_count)
        """
        temp_entries = list(self._stream._entries)
        retained = self._stream._retained_bytes
        dropped_cap = 0
        dropped_mem = 0

        for entry in batch:
            cost = len(entry.payload.encode("utf-8"))
            while len(temp_entries) >= self._stream._max_entries:
                old = temp_entries.pop(0)
                retained -= len(old.payload.encode("utf-8"))
                dropped_cap += 1
            while temp_entries and (retained + cost > self._stream._memory_budget_bytes):
                old = temp_entries.pop(0)
                retained -= len(old.payload.encode("utf-8"))
                dropped_mem += 1
            temp_entries.append(entry)
            retained += cost

        total_evicted = dropped_cap + dropped_mem
        return total_evicted, dropped_cap, dropped_mem

    def append_batch(self, entries: Sequence[StreamEntry]) -> tuple[int, int]:
        """Append a batch of StreamEntries, emitting row removal and insertion signals.

        Returns:
            Tuple of (inserted_count, evicted_count).
        """
        if not entries:
            return 0, 0

        total_evicted, dropped_cap, dropped_mem = self._calculate_batch_evictions(entries)

        if total_evicted > 0:
            self.beginRemoveRows(QModelIndex(), 0, total_evicted - 1)
            for _ in range(total_evicted):
                old = self._stream._entries.popleft()
                self._stream._retained_bytes -= len(old.payload.encode("utf-8"))
            self._stream._dropped_capacity += dropped_cap
            self._stream._dropped_memory_budget += dropped_mem
            self.endRemoveRows()
            logger.debug(
                "websocket_stream_model_eviction_signaled evicted=%d "
                "dropped_capacity=%d dropped_memory_budget=%d total_rows=%d",
                total_evicted,
                dropped_cap,
                dropped_mem,
                len(self._stream._entries),
            )

        old_len = len(self._stream._entries)
        self.beginInsertRows(QModelIndex(), old_len, old_len + len(entries) - 1)
        for entry in entries:
            self._stream._entries.append(entry)
            self._stream._retained_bytes += len(entry.payload.encode("utf-8"))
        self.endInsertRows()

        logger.debug(
            "websocket_stream_model_batch_appended inserted=%d evicted=%d total_rows=%d",
            len(entries),
            total_evicted,
            len(self._stream._entries),
        )

        return len(entries), total_evicted

    def clear(self) -> None:
        """Clear all entries in the model and underlying stream."""
        self.beginResetModel()
        self._stream.clear()
        self.endResetModel()
        logger.debug("websocket_stream_model_cleared")
