import logging
from typing import Literal

from PySide6.QtCore import QThread, Signal

from pypost.core.storage_interface import StorageInterface
from pypost.models.models import Environment

logger = logging.getLogger(__name__)


class EnvironmentStorageWorker(QThread):
    load_finished = Signal(list)
    load_failed = Signal(object)
    save_finished = Signal()
    save_failed = Signal(object)

    def __init__(
        self,
        storage: StorageInterface,
        *,
        operation: Literal["load", "save"],
        environments: list[Environment] | None = None,
    ) -> None:
        super().__init__()
        self._storage = storage
        self._operation = operation
        self._environments = environments

    def run(self) -> None:
        logger.debug("environment_storage_worker_run_started op=%s", self._operation)
        if self._operation == "load":
            self._run_load()
        else:
            self._run_save()

    def _run_load(self) -> None:
        try:
            environments = self._storage.load_environments()
            logger.debug(
                "environment_storage_worker_load_completed count=%d",
                len(environments),
            )
            self.load_finished.emit(environments)
        except Exception as exc:
            logger.error(
                "environment_storage_worker_load_failed error=%s",
                exc,
                exc_info=True,
            )
            self.load_failed.emit(exc)

    def _run_save(self) -> None:
        try:
            self._storage.save_environments(self._environments or [])
            logger.debug("environment_storage_worker_save_completed")
            self.save_finished.emit()
        except Exception as exc:
            logger.error(
                "environment_storage_worker_save_failed error=%s",
                exc,
                exc_info=True,
            )
            self.save_failed.emit(exc)
