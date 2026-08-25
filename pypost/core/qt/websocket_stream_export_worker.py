"""Background worker for WebSocket stream transcript file export (PYPOST-1144)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping

from PySide6.QtCore import QThread, Signal

from pypost.core.websocket_stream import StreamEntry
from pypost.core.websocket_stream_export import (
    StreamExportSnapshot,
    export_stream_to_json_file,
    export_stream_to_text_file,
)

logger = logging.getLogger(__name__)

ExportFormat = str  # "json" | "text"


class WebSocketStreamExportWorker(QThread):
    """Format and write a masked stream transcript off the GUI thread."""

    export_completed = Signal(str, str)  # path, format
    export_failed = Signal(str, object)  # format, error

    def __init__(
        self,
        path: Path,
        entries: tuple[StreamEntry, ...],
        dropped: Mapping[str, int],
        export_format: ExportFormat,
        *,
        env_vars: Mapping[str, str],
        hidden_keys: set[str],
    ) -> None:
        super().__init__()
        self._path = path
        self._entries = entries
        self._dropped = dict(dropped)
        self._export_format = export_format
        self._env_vars = dict(env_vars)
        self._hidden_keys = set(hidden_keys)

    def run(self) -> None:
        logger.debug(
            "websocket_stream_export_worker_started format=%s path=%s entries_count=%d",
            self._export_format,
            self._path,
            len(self._entries),
        )
        snapshot = StreamExportSnapshot(self._entries, self._dropped)
        try:
            if self._export_format == "json":
                export_stream_to_json_file(
                    self._path,
                    snapshot,
                    env_vars=self._env_vars,
                    hidden_keys=self._hidden_keys,
                )
            else:
                export_stream_to_text_file(
                    self._path,
                    snapshot,
                    env_vars=self._env_vars,
                    hidden_keys=self._hidden_keys,
                )
            logger.debug(
                "websocket_stream_export_worker_completed format=%s path=%s",
                self._export_format,
                self._path,
            )
            self.export_completed.emit(str(self._path), self._export_format)
        except Exception as exc:
            logger.error(
                "websocket_stream_export_worker_failed format=%s path=%s error=%s",
                self._export_format,
                self._path,
                exc,
                exc_info=True,
            )
            self.export_failed.emit(self._export_format, exc)
