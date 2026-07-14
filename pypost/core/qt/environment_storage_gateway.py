import logging
from typing import Literal

from PySide6.QtCore import QObject, Signal

from pypost.core.qt.environment_storage_worker import EnvironmentStorageWorker
from pypost.core.storage_interface import StorageInterface
from pypost.models.models import Environment

logger = logging.getLogger(__name__)


class EnvironmentStorageGateway(QObject):
    load_completed = Signal(list)
    load_failed = Signal(object)
    save_completed = Signal()
    save_failed = Signal(object)

    def __init__(self, storage: StorageInterface, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._storage = storage
        self._worker: EnvironmentStorageWorker | None = None
        self._pending_load = False
        self._pending_save: list[Environment] | None = None

    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def has_pending_work(self) -> bool:
        return self.is_busy() or self._pending_load or self._pending_save is not None

    def wait_idle(self, timeout_ms: int = 30000) -> bool:
        from PySide6.QtCore import QElapsedTimer
        from PySide6.QtWidgets import QApplication

        if not self.has_pending_work():
            return True

        timer = QElapsedTimer()
        timer.start()
        app = QApplication.instance()
        logger.info("environment_storage_gateway_wait_idle_started")
        while self.has_pending_work():
            if timer.elapsed() >= timeout_ms:
                logger.warning(
                    "environment_storage_gateway_wait_idle_timeout elapsed_ms=%d",
                    timer.elapsed(),
                )
                return False
            if app is not None:
                app.processEvents()
            elif self._worker is not None:
                self._worker.wait(10)
        logger.info(
            "environment_storage_gateway_wait_idle_completed elapsed_ms=%d",
            timer.elapsed(),
        )
        return True

    def load_async(self) -> None:
        if self.is_busy():
            self._pending_load = True
            logger.debug("environment_storage_gateway_load_queued")
            return
        self._start_operation("load")

    def save_async(self, environments: list[Environment]) -> None:
        snapshot = [env.model_copy(deep=True) for env in environments]
        if self.is_busy():
            self._pending_save = snapshot
            logger.debug("environment_storage_gateway_save_coalesced count=%d", len(snapshot))
            return
        self._start_operation("save", snapshot)

    def _start_operation(
        self,
        operation: Literal["load", "save"],
        environments: list[Environment] | None = None,
    ) -> None:
        self._worker = EnvironmentStorageWorker(
            self._storage,
            operation=operation,
            environments=environments,
        )
        if operation == "load":
            self._worker.load_finished.connect(self._on_load_finished)
            self._worker.load_failed.connect(self._on_load_failed)
        else:
            self._worker.save_finished.connect(self._on_save_finished)
            self._worker.save_failed.connect(self._on_save_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
        logger.debug("environment_storage_gateway_operation_started op=%s", operation)

    def _on_load_finished(self, environments: list) -> None:
        self.load_completed.emit(environments)

    def _on_load_failed(self, error: object) -> None:
        self.load_failed.emit(error)

    def _on_save_finished(self) -> None:
        self.save_completed.emit()

    def _on_save_failed(self, error: object) -> None:
        self.save_failed.emit(error)

    def _on_worker_finished(self) -> None:
        self._worker = None
        if self._pending_save is not None:
            pending = self._pending_save
            self._pending_save = None
            logger.info(
                "environment_storage_gateway_pending_save_started count=%d",
                len(pending),
            )
            self._start_operation("save", pending)
            return
        if self._pending_load:
            self._pending_load = False
            logger.info("environment_storage_gateway_pending_load_started")
            self._start_operation("load")
