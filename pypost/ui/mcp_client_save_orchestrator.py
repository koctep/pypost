"""Coordinates save and save-as persistence for MCP Client workspace tabs."""

from __future__ import annotations

import logging
import uuid

from PySide6.QtWidgets import QWidget

from pypost.core.mcp_client_persisted_fields import (
    persisted_mcp_client_fields_equal,
    snapshot_mcp_client_persisted_fields,
)
from pypost.core.mcp_client_registry import McpClientRegistry
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.qt.state_manager import StateManager
from pypost.models.mcp_client import McpClientConnection
from pypost.models.settings import AppSettings
from pypost.ui.collection_item_dialogs import (
    confirm_overwrite_newer_saved_version,
    confirm_overwrite_request,
)
from pypost.ui.dialogs.save_dialog import SaveRequestDialog
from pypost.ui.request_save_orchestrator import (
    SaveAction,
    SaveResult,
    StaleCheckContext,
)

logger = logging.getLogger(__name__)


class McpClientSaveOrchestrator:
    """Handles save/save-as dialogs, confirmations, and registry persistence."""

    def __init__(
        self,
        mcp_client_registry: McpClientRegistry,
        state_manager: StateManager,
        settings: AppSettings,
        metrics: MetricsTrackerProtocol | None = None,
    ) -> None:
        self._registry = mcp_client_registry
        self._state_manager = state_manager
        self._settings = settings
        self._metrics = resolve_metrics(metrics)

    def save_profile(
        self,
        connection: McpClientConnection,
        parent: QWidget,
        *,
        stale_context: StaleCheckContext | None = None,
    ) -> SaveResult:
        existing_result = self._registry.find_mcp_client(connection.id)

        if existing_result:
            existing_conn, found_collection = existing_result
            return self._save_overwrite(
                connection,
                existing_conn,
                found_collection.id,
                parent,
                stale_context=stale_context,
            )

        return self._save_new(connection, parent)

    def save_as_profile(
        self, connection: McpClientConnection, parent: QWidget
    ) -> SaveResult:
        logger.info("mcp_client_save_as_flow_started source_id=%s", connection.id)
        collections = self._registry.request_manager.get_collections()
        dialog = SaveRequestDialog(collections, parent)
        if not dialog.exec():
            logger.info(
                "mcp_client_save_as_flow_cancelled source_id=%s",
                connection.id,
            )
            return SaveResult(SaveAction.CANCELLED)

        target_collection_id = self._resolve_target_collection(dialog)
        if not target_collection_id:
            logger.warning(
                "mcp_client_save_as_flow_failed reason=missing_target_collection"
            )
            return SaveResult(SaveAction.CANCELLED)

        new_conn = connection.model_copy(
            deep=True,
            update={"id": str(uuid.uuid4()), "name": dialog.request_name},
        )
        self._registry.save_mcp_client(new_conn, target_collection_id)
        logger.info(
            "mcp_client_save_as_flow_completed source_id=%s new_id=%s"
            " target_collection_id=%s",
            connection.id,
            new_conn.id,
            target_collection_id,
        )
        self._ensure_collection_expanded(target_collection_id)
        return SaveResult(
            SaveAction.SAVE_AS,
            request=new_conn,
            collection_id=target_collection_id,
        )

    def _save_overwrite(
        self,
        connection: McpClientConnection,
        existing_conn: McpClientConnection,
        collection_id: str,
        parent: QWidget,
        *,
        stale_context: StaleCheckContext | None,
    ) -> SaveResult:
        if self._settings.confirm_overwrite_request:
            message = (
                "This will overwrite the existing MCP Client profile "
                f"'{existing_conn.name}'. Continue?"
            )
            if (
                stale_context
                and stale_context.persisted_baseline
                and not persisted_mcp_client_fields_equal(
                    stale_context.persisted_baseline,
                    existing_conn,
                )
            ):
                message = (
                    "A newer version of this MCP Client profile exists on disk. "
                    f"This will overwrite '{existing_conn.name}'. Continue?"
                )
            if not confirm_overwrite_request(parent, message):
                logger.info(
                    "mcp_client_save_overwrite_cancelled profile_id=%s",
                    connection.id,
                )
                return SaveResult(SaveAction.CANCELLED)

        if not self._confirm_stale_overwrite(parent, stale_context, existing_conn):
            logger.info(
                "mcp_client_save_stale_cancelled profile_id=%s",
                connection.id,
            )
            return SaveResult(SaveAction.CANCELLED)

        self._registry.save_mcp_client(connection, collection_id)
        logger.info(
            "mcp_client_save_overwrite_succeeded profile_id=%s collection_id=%s",
            connection.id,
            collection_id,
        )
        self._metrics.track_gui_save_action("overwrite")

        snapshot = snapshot_mcp_client_persisted_fields(connection)
        return SaveResult(
            SaveAction.OVERWRITE,
            request=snapshot,
            collection_id=collection_id,
        )

    def _save_new(
        self, connection: McpClientConnection, parent: QWidget
    ) -> SaveResult:
        collections = self._registry.request_manager.get_collections()
        dialog = SaveRequestDialog(collections, parent)
        if not dialog.exec():
            return SaveResult(SaveAction.CANCELLED)

        connection.name = dialog.request_name
        target_collection_id = self._resolve_target_collection(dialog)
        if not target_collection_id:
            logger.warning("mcp_client_save_failed reason=missing_target_collection")
            return SaveResult(SaveAction.CANCELLED)

        self._registry.save_mcp_client(connection, target_collection_id)
        logger.info(
            "mcp_client_save_new_succeeded profile_id=%s name=%s collection_id=%s",
            connection.id,
            connection.name,
            target_collection_id,
        )
        self._metrics.track_gui_save_action("new")

        self._ensure_collection_expanded(target_collection_id)
        return SaveResult(
            SaveAction.CREATED_NEW,
            request=connection,
            collection_id=target_collection_id,
        )

    def _resolve_target_collection(self, dialog: SaveRequestDialog) -> str | None:
        target_collection_id = dialog.selected_collection_id
        if not target_collection_id and dialog.new_collection_name:
            new_col = self._registry.request_manager.create_collection(
                dialog.new_collection_name
            )
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
        disk_conn: McpClientConnection,
    ) -> bool:
        if stale_context is None or stale_context.persisted_baseline is None:
            return True
        if persisted_mcp_client_fields_equal(
            stale_context.persisted_baseline, disk_conn
        ):
            return True
        if not stale_context.stale_persisted:
            return True
        return confirm_overwrite_newer_saved_version(parent)
