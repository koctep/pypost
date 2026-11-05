"""Background worker for library connection and remote manifest discovery."""
from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)


class ManifestDiscoveryWorker(QThread):
    """Enumerate library connections and manifest collections off the UI thread."""

    discovery_completed = Signal(object, int)
    discovery_failed = Signal(Exception, int)

    def __init__(
        self,
        library_service: Any,
        generation_id: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.library_service = library_service
        self.generation_id = generation_id
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        self.requestInterruption()
        logger.debug(
            "collection_variable_manifest_discovery_worker_cancelled generation_id=%d",
            self.generation_id,
        )

    def run(self) -> None:
        logger.debug(
            "collection_variable_manifest_discovery_worker_started generation_id=%d",
            self.generation_id,
        )
        try:
            connections = self.library_service.list_connections()
            entries: list[tuple[str, tuple[str, str, str]]] = []
            for conn in connections:
                if self._cancelled or self.isInterruptionRequested():
                    break
                manifest_cols = self.library_service.list_manifest_collections(
                    conn.stable_id
                )
                for mcol in manifest_cols:
                    if self._cancelled or self.isInterruptionRequested():
                        break
                    col_name = mcol.get("name") or mcol.get("path")
                    label = f"{col_name} ({conn.name or conn.stable_id})"
                    entries.append(
                        (label, ("library", conn.stable_id, mcol["path"])),
                    )

            if self._cancelled or self.isInterruptionRequested():
                logger.debug(
                    "collection_variable_manifest_discovery_worker_interrupted "
                    "generation_id=%d",
                    self.generation_id,
                )
                return

            logger.debug(
                "collection_variable_manifest_discovery_worker_completed "
                "generation_id=%d entry_count=%d",
                self.generation_id,
                len(entries),
            )
            self.discovery_completed.emit(entries, self.generation_id)
        except Exception as exc:
            if not self._cancelled and not self.isInterruptionRequested():
                logger.warning(
                    "collection_variable_manifest_discovery_worker_failed "
                    "generation_id=%d error=%s",
                    self.generation_id,
                    exc,
                )
                self.discovery_failed.emit(exc, self.generation_id)
            else:
                logger.debug(
                    "collection_variable_manifest_discovery_worker_interrupted_on_error "
                    "generation_id=%d error=%s",
                    self.generation_id,
                    exc,
                )
