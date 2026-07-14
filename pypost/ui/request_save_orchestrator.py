"""Coordinates save and save-as persistence flows for the request editor."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtWidgets import QWidget

from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.request_manager import RequestManager
from pypost.core.request_persisted_fields import (
    persisted_fields_equal,
    snapshot_persisted_fields,
)
from pypost.core.qt.state_manager import StateManager
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.ui.collection_item_dialogs import (
    confirm_overwrite_newer_saved_version,
    confirm_overwrite_request,
)
from pypost.ui.dialogs.save_dialog import SaveRequestDialog

logger = logging.getLogger(__name__)


class SaveAction(Enum):
    CANCELLED = auto()
    OVERWRITE = auto()
    CREATED_NEW = auto()
    SAVE_AS = auto()


@dataclass(frozen=True)
class StaleCheckContext:
    """Tab persistence state used before overwriting an existing request."""

    persisted_baseline: RequestData | None
    stale_persisted: bool


@dataclass(frozen=True)
class SaveResult:
    action: SaveAction
    request: RequestData | None = None
    collection_id: str | None = None


class RequestSaveOrchestrator:
    """Handles save/save-as dialogs, confirmations, and RequestManager persistence."""

    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        settings: AppSettings,
        metrics: MetricsTrackerProtocol | None = None,
    ) -> None:
        self._request_manager = request_manager
        self._state_manager = state_manager
        self._settings = settings
        self._metrics = resolve_metrics(metrics)

    def save_request(
        self,
        request_data: RequestData,
        parent: QWidget,
        *,
        stale_context: StaleCheckContext | None = None,
    ) -> SaveResult:
        existing_result = self._request_manager.find_request(request_data.id)

        if existing_result:
            existing_request, found_collection = existing_result
            return self._save_overwrite(
                request_data,
                existing_request,
                found_collection.id,
                parent,
                stale_context=stale_context,
            )

        return self._save_new(request_data, parent)

    def save_as_request(self, request_data: RequestData, parent: QWidget) -> SaveResult:
        logger.info("save_as_flow_started source_request_id=%s", request_data.id)
        collections = self._request_manager.get_collections()
        dialog = SaveRequestDialog(collections, parent)
        if not dialog.exec():
            logger.info("save_as_flow_cancelled source_request_id=%s", request_data.id)
            return SaveResult(SaveAction.CANCELLED)

        target_collection_id = self._resolve_target_collection(dialog)
        if not target_collection_id:
            logger.warning("save_as_flow_failed reason=missing_target_collection")
            return SaveResult(SaveAction.CANCELLED)

        new_request = request_data.model_copy(
            deep=True,
            update={"id": str(uuid.uuid4()), "name": dialog.request_name},
        )
        self._request_manager.save_request(new_request, target_collection_id)
        logger.info(
            "save_as_flow_completed source_request_id=%s new_request_id=%s"
            " target_collection_id=%s",
            request_data.id,
            new_request.id,
            target_collection_id,
        )
        self._ensure_collection_expanded(target_collection_id)
        return SaveResult(
            SaveAction.SAVE_AS,
            request=new_request,
            collection_id=target_collection_id,
        )

    def _save_overwrite(
        self,
        request_data: RequestData,
        existing_request: RequestData,
        collection_id: str,
        parent: QWidget,
        *,
        stale_context: StaleCheckContext | None,
    ) -> SaveResult:
        if self._settings.confirm_overwrite_request:
            message = (
                "This will overwrite the existing request "
                f"'{existing_request.name}'. Continue?"
            )
            if stale_context and stale_context.persisted_baseline and not persisted_fields_equal(
                stale_context.persisted_baseline,
                existing_request,
            ):
                message = (
                    "A newer version of this request exists on disk. "
                    f"This will overwrite '{existing_request.name}'. Continue?"
                )
            if not confirm_overwrite_request(parent, message):
                logger.info("save_request_overwrite_cancelled request_id=%s", request_data.id)
                return SaveResult(SaveAction.CANCELLED)

        if not self._confirm_stale_overwrite(parent, stale_context, existing_request):
            logger.info("save_request_stale_cancelled request_id=%s", request_data.id)
            return SaveResult(SaveAction.CANCELLED)

        self._request_manager.save_request(request_data, collection_id)
        logger.info(
            "save_request_overwrite_succeeded request_id=%s collection_id=%s",
            request_data.id,
            collection_id,
        )
        self._metrics.track_gui_save_action("overwrite")

        snapshot = snapshot_persisted_fields(request_data)
        return SaveResult(
            SaveAction.OVERWRITE,
            request=snapshot,
            collection_id=collection_id,
        )

    def _save_new(self, request_data: RequestData, parent: QWidget) -> SaveResult:
        collections = self._request_manager.get_collections()
        dialog = SaveRequestDialog(collections, parent)
        if not dialog.exec():
            return SaveResult(SaveAction.CANCELLED)

        request_data.name = dialog.request_name
        target_collection_id = self._resolve_target_collection(dialog)
        if not target_collection_id:
            logger.warning("save_request_failed reason=missing_target_collection")
            return SaveResult(SaveAction.CANCELLED)

        self._request_manager.save_request(request_data, target_collection_id)
        logger.info(
            "save_request_new_succeeded request_id=%s name=%s collection_id=%s",
            request_data.id,
            request_data.name,
            target_collection_id,
        )
        self._metrics.track_gui_save_action("new")

        self._ensure_collection_expanded(target_collection_id)
        return SaveResult(
            SaveAction.CREATED_NEW,
            request=request_data,
            collection_id=target_collection_id,
        )

    def _resolve_target_collection(self, dialog: SaveRequestDialog) -> str | None:
        target_collection_id = dialog.selected_collection_id
        if not target_collection_id and dialog.new_collection_name:
            new_col = self._request_manager.create_collection(dialog.new_collection_name)
            target_collection_id = new_col.id
        return target_collection_id

    def _ensure_collection_expanded(self, collection_id: str) -> None:
        current_expanded = self._state_manager.get_expanded_collections()
        if collection_id not in current_expanded:
            current_expanded.append(collection_id)
            self._state_manager.set_expanded_collections(current_expanded)

    def _confirm_stale_overwrite(
        self,
        parent: QWidget,
        stale_context: StaleCheckContext | None,
        disk_request: RequestData,
    ) -> bool:
        if stale_context is None or stale_context.persisted_baseline is None:
            return True
        if persisted_fields_equal(stale_context.persisted_baseline, disk_request):
            return True
        if not stale_context.stale_persisted:
            return True
        return confirm_overwrite_newer_saved_version(parent)
