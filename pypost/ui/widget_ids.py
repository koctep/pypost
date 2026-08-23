"""Stable Qt widget identities for agents and automated UI tests.

Primary contract: ``QObject.objectName``. For ``QWidget`` instances the same
string is mirrored on ``accessibleIdentifier`` when the Qt API is available.
Do not use ``accessibleName`` or visible label text as automation identities —
those may change with locale or copy edits.

See ``doc/dev/ui_identity.md`` for the naming convention and lookup rules.
"""

from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

# Key surfaces (PYPOST-834). Values are stable across theme/locale.
MAIN_WINDOW = "pypost_main_window"
COLLECTION_TREE = "pypost_collection_tree"
COLLECTION_IMPORT_BUTTON = "pypost_collection_import_button"
COLLECTION_EXPORT_BUTTON = "pypost_collection_export_button"
COLLECTION_EXPORT_ALL_BUTTON = "pypost_collection_export_all_button"
REQUEST_TABS = "pypost_request_tabs"
METHOD_COMBO = "pypost_method_combo"
URL_INPUT = "pypost_url_input"
SEND_BUTTON = "pypost_send_button"
REQUEST_BODY_EDIT = "pypost_request_body_edit"
REQUEST_DETAIL_TABS = "pypost_request_detail_tabs"
RESPONSE_PANEL = "pypost_response_panel"
RESPONSE_STATUS = "pypost_response_status"
RESPONSE_BODY = "pypost_response_body"
ENV_BAR = "pypost_env_bar"
ENV_SELECTOR = "pypost_env_selector"
ENV_MANAGE_BUTTON = "pypost_env_manage_button"
ENV_IMPORT_BUTTON = "pypost_env_import_button"
ENV_EXPORT_BUTTON = "pypost_env_export_button"
SETTINGS_BUTTON = "pypost_settings_button"
SETTINGS_DIALOG = "pypost_settings_dialog"
PLUS_TAB_PLACEHOLDER = "pypost_plus_tab_placeholder"
PLUS_TAB_BUTTON = "pypost_plus_tab_button"

# WebSocket session surfaces (PYPOST-1132 / WS-4).
WS_TAB_PAGE = "pypost_ws_tab_page"
WS_URL_INPUT = "pypost_ws_url_input"
WS_CONNECT_BUTTON = "pypost_ws_connect_button"
WS_STATE_BADGE = "pypost_ws_state_badge"
WS_PARAMS_TABLE = "pypost_ws_params_table"
WS_HEADERS_TABLE = "pypost_ws_headers_table"
WS_SUBPROTOCOLS_INPUT = "pypost_ws_subprotocols_input"
WS_STREAM_VIEW = "pypost_ws_stream_view"
WS_COMPOSER_EDIT = "pypost_ws_composer_edit"
WS_SEND_MESSAGE_BUTTON = "pypost_ws_send_message_button"
WS_LOCK_NOTICE = "pypost_ws_lock_notice"
WS_DETAIL_TABS = "pypost_ws_detail_tabs"
# WebSocket stream inspector surfaces (PYPOST-1133 / WS-5).
WS_STREAM_SEARCH_INPUT = "pypost_ws_stream_search_input"
WS_STREAM_DIRECTION_FILTER = "pypost_ws_stream_direction_filter"
WS_STREAM_KIND_FILTER = "pypost_ws_stream_kind_filter"
WS_STREAM_PAUSE_BUTTON = "pypost_ws_stream_pause_button"
WS_STREAM_CLEAR_BUTTON = "pypost_ws_stream_clear_button"
WS_STREAM_EXPORT_BUTTON = "pypost_ws_stream_export_button"
WS_STREAM_DROP_NOTICE = "pypost_ws_stream_drop_notice"
WS_STREAM_DETAIL = "pypost_ws_stream_detail"
WS_STREAM_CLEAR_FILTER_BUTTON = "pypost_ws_stream_clear_filter_button"
WS_STREAM_MATCH_COUNT = "pypost_ws_stream_match_count"
WS_STREAM_DETAIL_COPY_BUTTON = "pypost_ws_stream_detail_copy_button"
WS_STREAM_DETAIL_SET_VAR_BUTTON = "pypost_ws_stream_detail_set_var_button"
WS_STREAM_DETAIL_WRAP_BUTTON = "pypost_ws_stream_detail_wrap_button"
WS_STREAM_DETAIL_HEX_BUTTON = "pypost_ws_stream_detail_hex_button"
WS_STREAM_FOLLOW_TAIL_BADGE = "pypost_ws_stream_follow_tail_badge"

KEY_WIDGET_IDS = (
    MAIN_WINDOW,
    COLLECTION_TREE,
    REQUEST_TABS,
    METHOD_COMBO,
    URL_INPUT,
    SEND_BUTTON,
    REQUEST_BODY_EDIT,
    REQUEST_DETAIL_TABS,
    RESPONSE_PANEL,
    RESPONSE_STATUS,
    RESPONSE_BODY,
    ENV_BAR,
    ENV_SELECTOR,
    ENV_MANAGE_BUTTON,
    SETTINGS_BUTTON,
    WS_TAB_PAGE,
    WS_URL_INPUT,
    WS_CONNECT_BUTTON,
    WS_STATE_BADGE,
    WS_PARAMS_TABLE,
    WS_HEADERS_TABLE,
    WS_SUBPROTOCOLS_INPUT,
    WS_STREAM_VIEW,
    WS_COMPOSER_EDIT,
    WS_SEND_MESSAGE_BUTTON,
    WS_LOCK_NOTICE,
    WS_DETAIL_TABS,
    WS_STREAM_SEARCH_INPUT,
    WS_STREAM_DIRECTION_FILTER,
    WS_STREAM_KIND_FILTER,
    WS_STREAM_PAUSE_BUTTON,
    WS_STREAM_CLEAR_BUTTON,
    WS_STREAM_EXPORT_BUTTON,
    WS_STREAM_DROP_NOTICE,
    WS_STREAM_DETAIL,
    WS_STREAM_CLEAR_FILTER_BUTTON,
    WS_STREAM_MATCH_COUNT,
    WS_STREAM_DETAIL_COPY_BUTTON,
    WS_STREAM_DETAIL_SET_VAR_BUTTON,
    WS_STREAM_DETAIL_WRAP_BUTTON,
    WS_STREAM_DETAIL_HEX_BUTTON,
    WS_STREAM_FOLLOW_TAIL_BADGE,
)


def set_widget_id(widget: QObject, widget_id: str) -> None:
    """Set ``objectName`` and mirror ``accessibleIdentifier`` on QWidgets."""
    widget.setObjectName(widget_id)
    if isinstance(widget, QWidget):
        setter = getattr(widget, "setAccessibleIdentifier", None)
        if callable(setter):
            setter(widget_id)
