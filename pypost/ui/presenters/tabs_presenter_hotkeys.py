"""Tab-kind-aware global hotkey routing for TabsPresenter (PYPOST-1162)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QWidget

from pypost.models.mcp_client import McpClientSessionState
from pypost.ui.widgets.mcp_client import McpClientTab
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter


def active_tab_kind(presenter: TabsPresenter) -> TabProtocol | None:
    """Return the protocol kind of the active workspace tab, if any."""
    tab = presenter._tabs.currentWidget()
    if isinstance(tab, WebSocketTab):
        return TabProtocol.WEBSOCKET
    if isinstance(tab, McpClientTab):
        return TabProtocol.MCP_CLIENT
    if _is_request_tab(tab):
        return TabProtocol.HTTP
    return None


def current_request_tab(presenter: TabsPresenter) -> RequestTab | None:
    tab = presenter._tabs.currentWidget()
    return tab if _is_request_tab(tab) else None


def current_websocket_tab(presenter: TabsPresenter) -> WebSocketTab | None:
    tab = presenter._tabs.currentWidget()
    return tab if isinstance(tab, WebSocketTab) else None


def current_mcp_client_tab(presenter: TabsPresenter) -> McpClientTab | None:
    tab = presenter._tabs.currentWidget()
    return tab if isinstance(tab, McpClientTab) else None


def handle_send_request_global(presenter: TabsPresenter) -> None:
    """Route F5 / Ctrl+Return to MCP/WS connect/invoke/send or HTTP send."""
    mcp_tab = current_mcp_client_tab(presenter)
    if mcp_tab is not None:
        handle_mcp_client_send_global(presenter)
        return
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is not None:
        handle_websocket_send_global(presenter)
        return
    tab = current_request_tab(presenter)
    if tab is not None:
        tab.request_editor.on_send()


def handle_websocket_connect_global(presenter: TabsPresenter) -> None:
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is None or ws_tab.presenter is None:
        return
    ws_tab.presenter._on_connect_clicked()


def handle_websocket_send_global(presenter: TabsPresenter) -> None:
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is None or ws_tab.presenter is None:
        return
    if _focus_in_composer(ws_tab):
        ws_tab.presenter.handle_send_message()
    else:
        handle_websocket_connect_global(presenter)


def handle_websocket_format_json_global(presenter: TabsPresenter) -> None:
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is None:
        return
    ws_tab.composer.format_json_payload()


def handle_mcp_client_connect_global(presenter: TabsPresenter) -> None:
    mcp_tab = current_mcp_client_tab(presenter)
    if mcp_tab is None:
        return
    state = mcp_tab.presenter.state
    if state in (
        McpClientSessionState.CONNECTED,
        McpClientSessionState.CONNECTING,
    ):
        mcp_tab.presenter.disconnect_requested()
    else:
        mcp_tab.presenter.connect_requested()


def handle_mcp_client_invoke_global(presenter: TabsPresenter) -> None:
    mcp_tab = current_mcp_client_tab(presenter)
    if mcp_tab is None:
        return
    mcp_tab.presenter.invoke_requested()


def handle_mcp_client_send_global(presenter: TabsPresenter) -> None:
    mcp_tab = current_mcp_client_tab(presenter)
    if mcp_tab is None:
        return
    if _focus_in_invoke_form(mcp_tab):
        handle_mcp_client_invoke_global(presenter)
    else:
        handle_mcp_client_connect_global(presenter)


def handle_focus_url(presenter: TabsPresenter) -> None:
    mcp_tab = current_mcp_client_tab(presenter)
    if mcp_tab is not None:
        url_input = mcp_tab.url_input
        url_input.setFocus()
        url_input.selectAll()
        return
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is not None:
        url_input = ws_tab.connection_editor.url_input
        url_input.setFocus()
        url_input.selectAll()
        return
    tab = current_request_tab(presenter)
    if tab is not None:
        tab.request_editor.url_input.setFocus()
        tab.request_editor.url_input.selectAll()


def handle_switch_to_params_global(presenter: TabsPresenter) -> None:
    tab = current_request_tab(presenter)
    if tab is not None:
        tab.request_editor.detail_tabs.setCurrentIndex(0)


def handle_switch_to_headers_global(presenter: TabsPresenter) -> None:
    tab = current_request_tab(presenter)
    if tab is not None:
        tab.request_editor.detail_tabs.setCurrentIndex(1)


def handle_switch_to_body_global(presenter: TabsPresenter) -> None:
    tab = current_request_tab(presenter)
    if tab is not None:
        tab.request_editor.detail_tabs.setCurrentIndex(2)


def handle_switch_to_script_global(presenter: TabsPresenter) -> None:
    tab = current_request_tab(presenter)
    if tab is not None:
        tab.request_editor.detail_tabs.setCurrentIndex(3)


def _is_request_tab(tab: object) -> bool:
    from pypost.ui.presenters.tabs_presenter import RequestTab

    return isinstance(tab, RequestTab)


def _focus_in_composer(ws_tab: WebSocketTab) -> bool:
    focus = QApplication.focusWidget()
    if focus is None:
        return False
    composer = ws_tab.composer
    if focus is composer.payload_edit:
        return True
    return _is_descendant(composer, focus)


def _focus_in_invoke_form(mcp_tab: McpClientTab) -> bool:
    focus = QApplication.focusWidget()
    if focus is None:
        return False
    invoke_form = mcp_tab.invoke_form
    return _is_descendant(invoke_form, focus)


def _is_descendant(ancestor: QWidget, widget: QWidget | None) -> bool:
    current = widget
    while current is not None:
        if current is ancestor:
            return True
        current = current.parentWidget()
    return False
