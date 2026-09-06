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
SETTINGS_TABS = "pypost_settings_tabs"
PLUS_TAB_PLACEHOLDER = "pypost_plus_tab_placeholder"
PLUS_TAB_BUTTON = "pypost_plus_tab_button"
NEW_TAB_PROTOCOL_MENU = "pypost_new_tab_protocol_menu"
MCP_CLIENT_TAB_PAGE = "pypost_mcp_client_tab_page"
MCP_CLIENT_URL_INPUT = "pypost_mcp_client_url_input"
MCP_CLIENT_CONNECT_BUTTON = "pypost_mcp_client_connect_button"
MCP_CLIENT_DISCONNECT_BUTTON = "pypost_mcp_client_disconnect_button"
MCP_CLIENT_STATE_BADGE = "pypost_mcp_client_state_badge"
MCP_CLIENT_TOOL_BROWSER = "pypost_mcp_client_tool_browser"
MCP_CLIENT_HEADERS_TABLE = "pypost_mcp_client_headers_table"
MCP_CLIENT_REFRESH_BUTTON = "pypost_mcp_client_refresh_button"
MCP_CLIENT_ERROR_LABEL = "pypost_mcp_client_error_label"
MCP_CLIENT_INVOKE_BUTTON = "pypost_mcp_client_invoke_button"
MCP_CLIENT_ARG_FORM = "pypost_mcp_client_arg_form"
MCP_CLIENT_ARG_JSON = "pypost_mcp_client_arg_json"
MCP_CLIENT_RESULT_PANE = "pypost_mcp_client_result_pane"
MCP_CLIENT_ELAPSED_LABEL = "pypost_mcp_client_elapsed_label"

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

# WebSocket composer & presets surfaces (PYPOST-1134 / WS-6).
WS_COMPOSER_FORMAT_COMBO = "pypost_ws_composer_format_combo"
WS_PRESET_COMBO = "pypost_ws_preset_combo"
WS_PRESET_SAVE_BUTTON = "pypost_ws_preset_save_button"
WS_SEQUENCE_COMBO = "pypost_ws_sequence_combo"
WS_SEQUENCE_RUN_BUTTON = "pypost_ws_sequence_run_button"
WS_SEQUENCE_STOP_BUTTON = "pypost_ws_sequence_stop_button"
WS_MESSAGES_TAB = "pypost_ws_messages_tab"
WS_PRESETS_LIST = "pypost_ws_presets_list"
WS_PRESET_NAME_INPUT = "pypost_ws_preset_name_input"
WS_PRESET_FORMAT_COMBO = "pypost_ws_preset_format_combo"
WS_PRESET_PAYLOAD_EDIT = "pypost_ws_preset_payload_edit"
WS_PRESET_NEW_BUTTON = "pypost_ws_preset_new_button"
WS_PRESET_DUPLICATE_BUTTON = "pypost_ws_preset_duplicate_button"
WS_PRESET_DELETE_BUTTON = "pypost_ws_preset_delete_button"
WS_PRESET_LOAD_BUTTON = "pypost_ws_preset_load_button"
WS_PRESET_SEND_BUTTON = "pypost_ws_preset_send_button"
WS_SEQUENCES_LIST = "pypost_ws_sequences_list"
WS_SEQUENCE_NEW_BUTTON = "pypost_ws_sequence_new_button"
WS_SEQUENCE_DUPLICATE_BUTTON = "pypost_ws_sequence_duplicate_button"
WS_SEQUENCE_DELETE_BUTTON = "pypost_ws_sequence_delete_button"
WS_SEQUENCE_STEPS_TABLE = "pypost_ws_sequence_steps_table"
WS_SEQUENCE_STEP_ADD_BUTTON = "pypost_ws_sequence_step_add_button"
WS_SEQUENCE_STEP_REMOVE_BUTTON = "pypost_ws_sequence_step_remove_button"
WS_SEQUENCE_STEP_UP_BUTTON = "pypost_ws_sequence_step_up_button"
WS_SEQUENCE_STEP_DOWN_BUTTON = "pypost_ws_sequence_step_down_button"

# Collection Library surfaces (PYPOST-1223).
LIBRARY_MANAGER_BUTTON = "pypost_library_manager_button"
LIBRARY_MANAGER_DIALOG = "pypost_library_manager_dialog"
LIBRARY_LIST = "pypost_library_list"
LIBRARY_CLONE_BUTTON = "pypost_library_clone_button"
LIBRARY_CONNECT_BUTTON = "pypost_library_connect_button"
LIBRARY_SEARCH_INPUT = "pypost_library_search_input"
LIBRARY_CLEAR_SEARCH_BUTTON = "pypost_library_clear_search_button"
LIBRARY_STATUS_FILTER = "pypost_library_status_filter"
LIBRARY_CLEAR_FILTER_BUTTON = "pypost_library_clear_filter_button"
LIBRARY_SORT_COMBO = "pypost_library_sort_combo"
LIBRARY_PULL_BUTTON = "pypost_library_pull_button"
LIBRARY_COMMIT_PUSH_BUTTON = "pypost_library_commit_push_button"
LIBRARY_SWITCH_BRANCH_BUTTON = "pypost_library_switch_branch_button"
LIBRARY_DELETE_BUTTON = "pypost_library_delete_button"
LIBRARY_REFRESH_BUTTON = "pypost_library_refresh_button"
LIBRARY_COPY_PATH_BUTTON = "pypost_library_copy_path_button"
LIBRARY_DISCONNECT_BUTTON = "pypost_library_disconnect_button"
LIBRARY_DIRTY_BADGE = "pypost_library_dirty_badge"
LIBRARY_BRANCH_BADGE = "pypost_library_branch_badge"
LIBRARY_SYNC_BADGE = "pypost_library_sync_badge"
LIBRARY_COLLECTIONS_LIST = "pypost_library_collections_list"
LIBRARY_CLONE_DIALOG = "pypost_library_clone_dialog"
LIBRARY_COMMIT_PUSH_DIALOG = "pypost_library_commit_push_dialog"
LIBRARY_DIRTY_PULL_WARNING_DIALOG = "pypost_library_dirty_pull_warning_dialog"
LIBRARY_BRANCH_SWITCH_DIALOG = "pypost_library_branch_switch_dialog"

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
    WS_COMPOSER_FORMAT_COMBO,
    WS_PRESET_COMBO,
    WS_PRESET_SAVE_BUTTON,
    WS_SEQUENCE_COMBO,
    WS_SEQUENCE_RUN_BUTTON,
    WS_SEQUENCE_STOP_BUTTON,
    WS_MESSAGES_TAB,
    WS_PRESETS_LIST,
    WS_PRESET_NAME_INPUT,
    WS_PRESET_FORMAT_COMBO,
    WS_PRESET_PAYLOAD_EDIT,
    WS_PRESET_NEW_BUTTON,
    WS_PRESET_DUPLICATE_BUTTON,
    WS_PRESET_DELETE_BUTTON,
    WS_PRESET_LOAD_BUTTON,
    WS_PRESET_SEND_BUTTON,
    WS_SEQUENCES_LIST,
    WS_SEQUENCE_NEW_BUTTON,
    WS_SEQUENCE_DUPLICATE_BUTTON,
    WS_SEQUENCE_DELETE_BUTTON,
    WS_SEQUENCE_STEPS_TABLE,
    WS_SEQUENCE_STEP_ADD_BUTTON,
    WS_SEQUENCE_STEP_REMOVE_BUTTON,
    WS_SEQUENCE_STEP_UP_BUTTON,
    WS_SEQUENCE_STEP_DOWN_BUTTON,
)


def set_widget_id(widget: QObject, widget_id: str) -> None:
    """Set ``objectName`` and mirror ``accessibleIdentifier`` on QWidgets."""
    widget.setObjectName(widget_id)
    if isinstance(widget, QWidget):
        setter = getattr(widget, "setAccessibleIdentifier", None)
        if callable(setter):
            setter(widget_id)
