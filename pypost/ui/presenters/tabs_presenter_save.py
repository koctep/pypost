"""Save and clipboard callbacks for :class:`TabsPresenter`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pypost.core.request_persisted_fields import snapshot_persisted_fields
from pypost.ui.presenters.tab_dirty import (
    connection_snapshot_from_tab,
    mcp_client_snapshot_from_tab,
)
from pypost.ui.request_save_orchestrator import SaveAction

if TYPE_CHECKING:
    from pypost.models.mcp_client import McpClientConnection
    from pypost.models.models import RequestData
    from pypost.models.websocket import WebSocketConnection
    from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter
    from pypost.ui.widgets.mcp_client import McpClientTab
    from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab


def _presenter_logger():
    """Resolve the established TabsPresenter logger at call time.

    Keeping this lookup dynamic preserves tests and integrations that patch
    ``tabs_presenter.logger`` after the save helpers have been imported.
    """
    from pypost.ui.presenters import tabs_presenter

    return tabs_presenter.logger


def save_mcp_client(
    presenter: TabsPresenter,
    source_tab: McpClientTab,
    connection: McpClientConnection,
) -> None:
    if not presenter._admission_open():
        return
    snapshot = mcp_client_snapshot_from_tab(source_tab)
    result = presenter._mcp_save_orchestrator.save_profile(
        snapshot,
        presenter._tabs,
        stale_context=presenter._stale_context_for_mcp_client_tab(source_tab),
    )
    if result.action == SaveAction.CANCELLED:
        return

    if result.action == SaveAction.OVERWRITE:
        saved = result.request
        if saved is None:
            _presenter_logger().error(
                "mcp_client_save_overwrite_failed reason=missing_snapshot profile_id=%s",
                connection.id,
            )
            return
        presenter._apply_mcp_save_result_to_tab(source_tab, saved)
        presenter.mcp_client_persisted.emit(connection.id, saved, source_tab)
        tab_index = presenter._index_of_tab(source_tab)
        if tab_index is not None:
            presenter._header.set_tab_label(tab_index, saved.name)
        presenter.mcp_client_saved.emit()
        return

    if result.action == SaveAction.CREATED_NEW and result.request is not None:
        tab_index = presenter._index_of_tab(source_tab)
        if tab_index is not None:
            presenter._header.set_tab_label(tab_index, result.request.name)
        presenter._apply_mcp_save_result_to_tab(source_tab, result.request)
        presenter.save_tabs_state()
        presenter.mcp_client_saved.emit()


def save_as_mcp_client(
    presenter: TabsPresenter,
    source_tab: McpClientTab,
    connection: McpClientConnection,
) -> None:
    del connection
    if not presenter._admission_open():
        return
    snapshot = mcp_client_snapshot_from_tab(source_tab)
    result = presenter._mcp_save_orchestrator.save_as_profile(snapshot, presenter._tabs)
    if result.action != SaveAction.SAVE_AS or result.request is None:
        return

    new_conn = result.request
    tab_index = presenter._index_of_tab(source_tab)
    if tab_index is not None:
        presenter._header.set_tab_label(tab_index, new_conn.name)
    presenter._apply_mcp_save_result_to_tab(source_tab, new_conn)
    presenter.save_tabs_state()
    presenter.mcp_client_save_as_completed.emit(new_conn, result.collection_id or "")


def save_websocket(
    presenter: TabsPresenter,
    source_tab: WebSocketTab,
    connection: WebSocketConnection,
) -> None:
    if not presenter._admission_open():
        return
    snapshot = connection_snapshot_from_tab(source_tab)
    result = presenter._ws_save_orchestrator.save_profile(
        snapshot,
        presenter._tabs,
        stale_context=presenter._stale_context_for_websocket_tab(source_tab),
    )
    if result.action == SaveAction.CANCELLED:
        return

    if result.action == SaveAction.OVERWRITE:
        saved = result.request
        if saved is None:
            _presenter_logger().error(
                "ws_save_overwrite_failed reason=missing_snapshot ws_id=%s",
                connection.id,
            )
            return
        presenter._apply_ws_save_result_to_tab(source_tab, saved)
        presenter.websocket_persisted.emit(connection.id, saved, source_tab)
        tab_index = presenter._index_of_tab(source_tab)
        if tab_index is not None:
            presenter._header.set_tab_label(tab_index, saved.name)
        presenter.websocket_saved.emit()
        return

    if result.action == SaveAction.CREATED_NEW and result.request is not None:
        tab_index = presenter._index_of_tab(source_tab)
        if tab_index is not None:
            presenter._header.set_tab_label(tab_index, result.request.name)
        presenter._apply_ws_save_result_to_tab(source_tab, result.request)
        presenter.save_tabs_state()
        presenter.websocket_saved.emit()


def save_as_websocket(
    presenter: TabsPresenter,
    source_tab: WebSocketTab,
    connection: WebSocketConnection,
) -> None:
    del connection
    if not presenter._admission_open():
        return
    snapshot = connection_snapshot_from_tab(source_tab)
    result = presenter._ws_save_orchestrator.save_as_profile(snapshot, presenter._tabs)
    if result.action != SaveAction.SAVE_AS or result.request is None:
        return

    new_conn = result.request
    tab_index = presenter._index_of_tab(source_tab)
    if tab_index is not None:
        presenter._header.set_tab_label(tab_index, new_conn.name)
    presenter._apply_ws_save_result_to_tab(source_tab, new_conn)
    presenter.save_tabs_state()
    presenter.websocket_save_as_completed.emit(new_conn, result.collection_id or "")


def save_request(
    presenter: TabsPresenter,
    source_tab: RequestTab,
    request_data: RequestData,
) -> None:
    if not presenter._admission_open():
        return
    result = presenter._save_orchestrator.save_request(
        request_data,
        presenter._tabs,
        stale_context=presenter._stale_context_for_tab(source_tab),
    )
    if result.action == SaveAction.CANCELLED:
        return

    if result.action == SaveAction.OVERWRITE:
        snapshot = result.request
        if snapshot is None:
            _presenter_logger().error(
                "save_request_overwrite_failed reason=missing_snapshot request_id=%s",
                request_data.id,
            )
            return
        source_tab.request_data = snapshot
        source_tab.persisted_baseline = snapshot_persisted_fields(snapshot)
        source_tab.stale_persisted = False
        presenter.request_persisted.emit(request_data.id, snapshot, source_tab)
        presenter._sync_tab_labels_for_request(request_data.id, request_data.name)
        presenter.request_saved.emit()
        return

    if result.action == SaveAction.CREATED_NEW and result.request is not None:
        tab_index = presenter._index_of_tab(source_tab)
        if tab_index is not None:
            presenter._header.set_tab_label(tab_index, result.request.name)
        presenter._apply_save_result_to_tab(source_tab, result.request)
        presenter.save_tabs_state()
        presenter.request_saved.emit()


def save_as_request(
    presenter: TabsPresenter,
    source_tab: RequestTab,
    request_data: RequestData,
) -> None:
    if not presenter._admission_open():
        return
    result = presenter._save_orchestrator.save_as_request(request_data, presenter._tabs)
    if result.action != SaveAction.SAVE_AS or result.request is None:
        return

    new_request = result.request
    tab_index = presenter._index_of_tab(source_tab)
    if tab_index is not None:
        presenter._header.set_tab_label(tab_index, new_request.name)
    source_tab.request_data = new_request
    source_tab.request_editor.request_data = new_request
    presenter._apply_save_result_to_tab(source_tab, new_request)
    presenter.save_tabs_state()
    presenter.request_save_as_completed.emit(new_request, result.collection_id or "")
