"""Protocol for metrics tracking consumed by services, workers, and UI."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from pypost.models.errors import ErrorCategory


@runtime_checkable
class MetricsTrackerProtocol(Protocol):
    """Tracking surface for Prometheus counters — no server or MCP lifecycle."""

    def track_gui_send_click(self) -> None: ...

    def track_gui_save_action(self, source: str) -> None: ...

    def track_gui_save_as_action(self, source: str) -> None: ...

    def track_gui_new_tab_action(
        self, source: str, protocol: str = "unknown"
    ) -> None: ...

    def track_gui_copy_curl_action(self) -> None: ...

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None: ...

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None: ...

    def track_gui_library_operation(self, operation: str, outcome: str) -> None: ...

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None: ...

    def track_gui_method_body_autoswitch(self, method: str) -> None: ...

    def track_gui_variable_autocomplete_trigger(self, context: str) -> None: ...

    def track_gui_variable_autocomplete_selection(self, context: str) -> None: ...

    def track_gui_variable_autocomplete_feedback(
        self, context: str, status: str
    ) -> None: ...

    def track_gui_variable_autocomplete_environment_refresh(self, context: str) -> None: ...

    def track_request_sent(self, method: str) -> None: ...

    def track_response_received(self, method: str, status_code: str) -> None: ...

    def track_response_body_truncated(self, method: str) -> None: ...

    def track_mcp_request_received(self, method: str) -> None: ...

    def track_mcp_response_sent(self, method: str, status: str) -> None: ...

    def track_mcp_argument_validation_failure(
        self, stage: str, transport: str, declared_type: str
    ) -> None: ...

    def set_mcp_server_up(self, ready: bool) -> None: ...

    def set_mcp_server_instance_counts(self, counts: Mapping[str, int]) -> None: ...

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None: ...

    def track_mcp_active_env_changed(self) -> None: ...

    def track_mcp_param_default_applied(self, method: str) -> None: ...

    def track_mcp_client_connect(self, result: str) -> None: ...

    def track_mcp_client_list_tools(self, result: str, operation: str) -> None: ...

    def track_mcp_client_call_tool(self, result: str) -> None: ...

    def track_history_entry_appended(self, method: str) -> None: ...

    def track_history_load_into_editor(self) -> None: ...

    def track_lifecycle_teardown(
        self,
        owner: str,
        outcome: str,
        elapsed_seconds: float,
        active_count: int,
        pending_count: int,
    ) -> None: ...

    def track_lifecycle_event(
        self, owner: str, event: str, count: int = 1
    ) -> None: ...

    def track_environment_update_disposition(self, disposition: str) -> None: ...

    def track_history_io_failure(self, operation: str) -> None: ...

    def track_request_error(self, category: ErrorCategory) -> None: ...

    def track_yaml_to_json_conversion_failed(self) -> None: ...

    def track_history_record_error(self) -> None: ...

    def track_hidden_value_mask_applied(self, surface: str) -> None: ...

    def track_retry_attempt(self, method: str, status_category: str) -> None: ...

    def track_request_retry_exhaustion(self, endpoint: str) -> None: ...

    def track_template_expression_render_attempt(
        self,
        render_path: str,
        outcome: str,
    ) -> None: ...

    def track_template_expression_validation_failure(
        self,
        render_path: str,
        code: str,
        function_name: str | None = None,
    ) -> None: ...

    def track_template_expression_render_duration(
        self,
        render_path: str,
        duration_seconds: float,
    ) -> None: ...

    def track_variable_validation(self, result: str) -> None: ...

    def track_variable_validation_failure(self, reason: str) -> None: ...

    def track_environment_value_encryption(self) -> None: ...

    def track_environment_value_decryption(self) -> None: ...

    def track_environment_encryption_error(self, stage: str, reason: str) -> None: ...

    def track_websocket_session_opened(self, outcome: str) -> None: ...

    def track_websocket_session_closed(self, reason: str) -> None: ...

    def track_websocket_message(self, direction: str, kind: str) -> None: ...

    def track_websocket_message_bytes(self, direction: str, byte_count: int) -> None: ...

    def track_websocket_stream_entries_dropped(
        self, reason: str, count: int = 1
    ) -> None: ...

    def track_websocket_reconnect_attempt(self, outcome: str) -> None: ...

    def set_websocket_active_sessions(self, count: int) -> None: ...

    def track_websocket_session_start_refused(self, reason: str) -> None: ...

    def track_websocket_probe_duration(
        self, outcome: str, duration_seconds: float
    ) -> None: ...


class NullMetrics:
    """No-op metrics tracker — safe default when observability is not injected."""

    def track_gui_send_click(self) -> None:
        return None

    def track_gui_save_action(self, source: str) -> None:
        return None

    def track_gui_save_as_action(self, source: str) -> None:
        return None

    def track_gui_new_tab_action(
        self, source: str, protocol: str = "unknown"
    ) -> None:
        return None

    def track_gui_copy_curl_action(self) -> None:
        return None

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None:
        return None

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None:
        return None

    def track_gui_library_operation(self, operation: str, outcome: str) -> None:
        return None

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None:
        return None

    def track_gui_method_body_autoswitch(self, method: str) -> None:
        return None

    def track_gui_variable_autocomplete_trigger(self, context: str) -> None:
        return None

    def track_gui_variable_autocomplete_selection(self, context: str) -> None:
        return None

    def track_gui_variable_autocomplete_feedback(
        self, context: str, status: str
    ) -> None:
        return None

    def track_gui_variable_autocomplete_environment_refresh(self, context: str) -> None:
        return None

    def track_request_sent(self, method: str) -> None:
        return None

    def track_response_received(self, method: str, status_code: str) -> None:
        return None

    def track_response_body_truncated(self, method: str) -> None:
        return None

    def track_mcp_request_received(self, method: str) -> None:
        return None

    def track_mcp_response_sent(self, method: str, status: str) -> None:
        return None

    def track_mcp_argument_validation_failure(
        self, stage: str, transport: str, declared_type: str
    ) -> None:
        return None

    def set_mcp_server_up(self, ready: bool) -> None:
        return None

    def set_mcp_server_instance_counts(self, counts: Mapping[str, int]) -> None:
        return None

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None:
        return None

    def track_mcp_active_env_changed(self) -> None:
        return None

    def track_mcp_param_default_applied(self, method: str) -> None:
        return None

    def track_mcp_client_connect(self, result: str) -> None:
        return None

    def track_mcp_client_list_tools(self, result: str, operation: str) -> None:
        return None

    def track_mcp_client_call_tool(self, result: str) -> None:
        return None

    def track_history_entry_appended(self, method: str) -> None:
        return None

    def track_history_load_into_editor(self) -> None:
        return None

    def track_lifecycle_teardown(
        self,
        owner: str,
        outcome: str,
        elapsed_seconds: float,
        active_count: int,
        pending_count: int,
    ) -> None:
        return None

    def track_lifecycle_event(
        self, owner: str, event: str, count: int = 1
    ) -> None:
        return None

    def track_environment_update_disposition(self, disposition: str) -> None:
        return None

    def track_history_io_failure(self, operation: str) -> None:
        return None

    def track_request_error(self, category: ErrorCategory) -> None:
        return None

    def track_yaml_to_json_conversion_failed(self) -> None:
        return None

    def track_history_record_error(self) -> None:
        return None

    def track_hidden_value_mask_applied(self, surface: str) -> None:
        return None

    def track_retry_attempt(self, method: str, status_category: str) -> None:
        return None

    def track_request_retry_exhaustion(self, endpoint: str) -> None:
        return None

    def track_template_expression_render_attempt(
        self,
        render_path: str,
        outcome: str,
    ) -> None:
        return None

    def track_template_expression_validation_failure(
        self,
        render_path: str,
        code: str,
        function_name: str | None = None,
    ) -> None:
        return None

    def track_template_expression_render_duration(
        self,
        render_path: str,
        duration_seconds: float,
    ) -> None:
        return None

    def track_variable_validation(self, result: str) -> None:
        return None

    def track_variable_validation_failure(self, reason: str) -> None:
        return None

    def track_environment_value_encryption(self) -> None:
        return None

    def track_environment_value_decryption(self) -> None:
        return None

    def track_environment_encryption_error(self, stage: str, reason: str) -> None:
        return None

    def track_websocket_session_opened(self, outcome: str) -> None:
        return None

    def track_websocket_session_closed(self, reason: str) -> None:
        return None

    def track_websocket_message(self, direction: str, kind: str) -> None:
        return None

    def track_websocket_message_bytes(self, direction: str, byte_count: int) -> None:
        return None

    def track_websocket_stream_entries_dropped(
        self, reason: str, count: int = 1
    ) -> None:
        return None

    def track_websocket_reconnect_attempt(self, outcome: str) -> None:
        return None

    def set_websocket_active_sessions(self, count: int) -> None:
        return None

    def track_websocket_session_start_refused(self, reason: str) -> None:
        return None

    def track_websocket_probe_duration(
        self, outcome: str, duration_seconds: float
    ) -> None:
        return None


NULL_METRICS: MetricsTrackerProtocol = NullMetrics()


def resolve_metrics(metrics: MetricsTrackerProtocol | None) -> MetricsTrackerProtocol:
    """Return ``metrics`` or a shared no-op instance when omitted."""
    return metrics if metrics is not None else NULL_METRICS
