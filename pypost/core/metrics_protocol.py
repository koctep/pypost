"""Protocol for metrics tracking consumed by services, workers, and UI."""

from typing import Protocol, runtime_checkable

from pypost.models.errors import ErrorCategory


@runtime_checkable
class MetricsTrackerProtocol(Protocol):
    """Tracking surface for Prometheus counters — no server or MCP lifecycle."""

    def track_gui_send_click(self) -> None: ...

    def track_gui_save_action(self, source: str) -> None: ...

    def track_gui_save_as_action(self, source: str) -> None: ...

    def track_gui_new_tab_action(self, source: str) -> None: ...

    def track_gui_copy_curl_action(self) -> None: ...

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None: ...

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None: ...

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None: ...

    def track_gui_method_body_autoswitch(self, method: str) -> None: ...

    def track_request_sent(self, method: str) -> None: ...

    def track_response_received(self, method: str, status_code: str) -> None: ...

    def track_response_body_truncated(self, method: str) -> None: ...

    def track_mcp_request_received(self, method: str) -> None: ...

    def track_mcp_response_sent(self, method: str, status: str) -> None: ...

    def set_mcp_server_up(self, ready: bool) -> None: ...

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None: ...

    def track_mcp_active_env_changed(self) -> None: ...

    def track_history_entry_appended(self, method: str) -> None: ...

    def track_history_load_into_editor(self) -> None: ...

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


class NullMetrics:
    """No-op metrics tracker — safe default when observability is not injected."""

    def track_gui_send_click(self) -> None:
        return None

    def track_gui_save_action(self, source: str) -> None:
        return None

    def track_gui_save_as_action(self, source: str) -> None:
        return None

    def track_gui_new_tab_action(self, source: str) -> None:
        return None

    def track_gui_copy_curl_action(self) -> None:
        return None

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None:
        return None

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None:
        return None

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None:
        return None

    def track_gui_method_body_autoswitch(self, method: str) -> None:
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

    def set_mcp_server_up(self, ready: bool) -> None:
        return None

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None:
        return None

    def track_mcp_active_env_changed(self) -> None:
        return None

    def track_history_entry_appended(self, method: str) -> None:
        return None

    def track_history_load_into_editor(self) -> None:
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


NULL_METRICS: MetricsTrackerProtocol = NullMetrics()


def resolve_metrics(metrics: MetricsTrackerProtocol | None) -> MetricsTrackerProtocol:
    """Return ``metrics`` or a shared no-op instance when omitted."""
    return metrics if metrics is not None else NULL_METRICS
