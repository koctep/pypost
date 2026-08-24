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

    def get_entry(self, row: int) -> StreamEntry:
        """Return the StreamEntry at the specified row index."""
        return self._stream[row]

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

    def append_batch(self, entries: Sequence[StreamEntry]) -> tuple[int, int]:
        """Append a batch of StreamEntries, emitting row removal and insertion signals.

        Returns:
            Tuple of (inserted_count, evicted_count).
        """
        if not entries:
            return 0, 0

        plan = self._stream.calculate_batch_evictions(entries)
        total_evicted = plan.total_evicted

        if plan.existing_evicted > 0:
            self.beginRemoveRows(QModelIndex(), 0, plan.existing_evicted - 1)
            self._stream.remove_front(plan.existing_evicted)
            self.endRemoveRows()

        self._stream.record_batch_drops(plan.dropped_capacity, plan.dropped_memory_budget)

        if total_evicted > 0:
            logger.debug(
                "websocket_stream_model_eviction_signaled evicted=%d "
                "dropped_capacity=%d dropped_memory_budget=%d total_rows=%d",
                total_evicted,
                plan.dropped_capacity,
                plan.dropped_memory_budget,
                len(self._stream),
            )

        if plan.entries_to_append:
            old_len = len(self._stream)
            self.beginInsertRows(
                QModelIndex(), old_len, old_len + len(plan.entries_to_append) - 1
            )
            self._stream.append_entries(plan.entries_to_append)
            self.endInsertRows()

        logger.debug(
            "websocket_stream_model_batch_appended inserted=%d evicted=%d total_rows=%d",
            len(entries),
            total_evicted,
            len(self._stream),
        )

        return len(entries), total_evicted

    def clear(self) -> None:
        """Clear all entries in the model and underlying stream."""
        self.beginResetModel()
        self._stream.clear()
        self.endResetModel()
        logger.debug("websocket_stream_model_cleared")
