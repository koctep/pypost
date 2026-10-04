"""Tab-kind-aware global hotkey routing for TabsPresenter (PYPOST-1162)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeGuard

from pypost.models.mcp_client import McpClientSessionState
from pypost.ui.widgets.mcp_client import McpClientTab
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter

logger = logging.getLogger(__name__)

# A route handler returns True when it ran its action, False when it returned early.
_RouteHandler = Callable[["TabsPresenter"], bool]
_Routes = dict[TabProtocol, tuple[str, _RouteHandler]]


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


def handle_f5_global(presenter: TabsPresenter) -> None:
    """Route F5: WS/MCP Connect / Disconnect, HTTP Send Request.

    Routing depends only on the active tab kind, never on keyboard focus.
    """
    _dispatch("f5", presenter, _F5_ROUTES)


def handle_ctrl_return_global(presenter: TabsPresenter) -> None:
    """Route Ctrl+Return: WS Send Message, MCP Invoke Tool, HTTP Send Request.

    Routing depends only on the active tab kind, never on keyboard focus.
    """
    _dispatch("ctrl_return", presenter, _CTRL_RETURN_ROUTES)


def handle_websocket_connect_global(presenter: TabsPresenter) -> bool:
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is None or ws_tab.presenter is None:
        return False
    ws_tab.presenter._on_connect_clicked()
    return True


def handle_websocket_send_message_global(presenter: TabsPresenter) -> bool:
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is None or ws_tab.presenter is None:
        return False
    ws_tab.presenter.handle_send_message()
    return True


def handle_websocket_format_json_global(presenter: TabsPresenter) -> None:
    ws_tab = current_websocket_tab(presenter)
    if ws_tab is None:
        return
    ws_tab.composer.format_json_payload()


def handle_mcp_client_connect_global(presenter: TabsPresenter) -> bool:
    mcp_tab = current_mcp_client_tab(presenter)
    if mcp_tab is None:
        return False
    state = mcp_tab.presenter.state
    if state in (
        McpClientSessionState.CONNECTED,
        McpClientSessionState.CONNECTING,
    ):
        mcp_tab.presenter.disconnect_requested()
    else:
        mcp_tab.presenter.connect_requested()
    return True


def handle_mcp_client_invoke_global(presenter: TabsPresenter) -> bool:
    mcp_tab = current_mcp_client_tab(presenter)
    if mcp_tab is None:
        return False
    mcp_tab.presenter.invoke_requested()
    return True


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


def _send_http_request(presenter: TabsPresenter) -> bool:
    tab = current_request_tab(presenter)
    if tab is None:
        return False
    tab.request_editor.on_send()
    return True


# Single source of truth for global send-key routing: tab kind -> (log label, handler).
_F5_ROUTES: _Routes = {
    TabProtocol.MCP_CLIENT: ("connect_toggle", handle_mcp_client_connect_global),
    TabProtocol.WEBSOCKET: ("connect_toggle", handle_websocket_connect_global),
    TabProtocol.HTTP: ("send_request", _send_http_request),
}
_CTRL_RETURN_ROUTES: _Routes = {
    TabProtocol.MCP_CLIENT: ("invoke_tool", handle_mcp_client_invoke_global),
    TabProtocol.WEBSOCKET: ("send_message", handle_websocket_send_message_global),
    TabProtocol.HTTP: ("send_request", _send_http_request),
}


def _dispatch(key: str, presenter: TabsPresenter, routes: _Routes) -> None:
    """Run the route for the active tab kind, then log what actually happened."""
    kind = active_tab_kind(presenter)
    route = None if kind is None else routes.get(kind)
    if route is None:
        _log_hotkey_routed(key, kind, "noop")
        return
    label, handler = route
    if handler(presenter):
        _log_hotkey_routed(key, kind, label)
    else:
        _log_hotkey_routed(key, kind, "noop", reason="target_unavailable")


def _log_hotkey_routed(
    key: str, kind: TabProtocol | None, action: str, reason: str | None = None
) -> None:
    """Record the outcome of a global send key (``action=noop`` when nothing ran)."""
    tab_kind = "none" if kind is None else kind.value
    if reason is None:
        logger.debug("hotkey_routed key=%s tab_kind=%s action=%s", key, tab_kind, action)
    else:
        logger.debug(
            "hotkey_routed key=%s tab_kind=%s action=%s reason=%s",
            key,
            tab_kind,
            action,
            reason,
        )


def _is_request_tab(tab: object) -> TypeGuard[RequestTab]:
    from pypost.ui.presenters.tabs_presenter import RequestTab

    return isinstance(tab, RequestTab)
