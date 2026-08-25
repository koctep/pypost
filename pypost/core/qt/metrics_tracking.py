from __future__ import annotations

from collections.abc import Mapping

from pypost.core.metrics_registry import MetricsRegistry
from pypost.models.errors import ErrorCategory


class MetricsTrackingMixin:
    """Explicit delegation for non-WebSocket metrics (PYPOST-1146)."""

    _registry: MetricsRegistry

    def track_gui_send_click(self) -> None:
        self._registry.track_gui_send_click()

    def track_gui_save_action(self, source: str) -> None:
        self._registry.track_gui_save_action(source)

    def track_gui_save_as_action(self, source: str) -> None:
        self._registry.track_gui_save_as_action(source)

    def track_gui_new_tab_action(self, source: str) -> None:
        self._registry.track_gui_new_tab_action(source)

    def track_gui_copy_curl_action(self) -> None:
        self._registry.track_gui_copy_curl_action()

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None:
        self._registry.track_gui_collection_delete_action(item_type, status)

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None:
        self._registry.track_gui_collection_rename_action(item_type, status)

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None:
        self._registry.track_gui_response_search_action(source, has_matches)

    def track_gui_method_body_autoswitch(self, method: str) -> None:
        self._registry.track_gui_method_body_autoswitch(method)

    def track_request_sent(self, method: str) -> None:
        self._registry.track_request_sent(method)

    def track_response_received(self, method: str, status_code: str) -> None:
        self._registry.track_response_received(method, status_code)

    def track_response_body_truncated(self, method: str) -> None:
        self._registry.track_response_body_truncated(method)

    def track_mcp_request_received(self, method: str) -> None:
        self._registry.track_mcp_request_received(method)

    def track_mcp_response_sent(self, method: str, status: str) -> None:
        self._registry.track_mcp_response_sent(method, status)

    def set_mcp_server_up(self, ready: bool) -> None:
        self._registry.set_mcp_server_up(ready)

    def set_mcp_server_instance_counts(self, counts: Mapping[str, int]) -> None:
        self._registry.set_mcp_server_instance_counts(counts)

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None:
        self._registry.track_mcp_tool_call_duration(method, status, duration_seconds)

    def track_mcp_active_env_changed(self) -> None:
        self._registry.track_mcp_active_env_changed()

    def track_mcp_param_default_applied(self, method: str) -> None:
        self._registry.track_mcp_param_default_applied(method)

    def track_history_entry_appended(self, method: str) -> None:
        self._registry.track_history_entry_appended(method)

    def track_history_load_into_editor(self) -> None:
        self._registry.track_history_load_into_editor()

    def track_request_error(self, category: ErrorCategory) -> None:
        self._registry.track_request_error(category)

    def track_yaml_to_json_conversion_failed(self) -> None:
        self._registry.track_yaml_to_json_conversion_failed()

    def track_history_record_error(self) -> None:
        self._registry.track_history_record_error()

    def track_hidden_value_mask_applied(self, surface: str) -> None:
        self._registry.track_hidden_value_mask_applied(surface)

    def track_retry_attempt(self, method: str, status_category: str) -> None:
        self._registry.track_retry_attempt(method, status_category)

    def track_request_retry_exhaustion(self, endpoint: str) -> None:
        self._registry.track_request_retry_exhaustion(endpoint)

    def track_template_expression_render_attempt(
        self,
        render_path: str,
        outcome: str,
    ) -> None:
        self._registry.track_template_expression_render_attempt(render_path, outcome)

    def track_template_expression_validation_failure(
        self,
        render_path: str,
        code: str,
        function_name: str | None = None,
    ) -> None:
        self._registry.track_template_expression_validation_failure(
            render_path, code, function_name
        )

    def track_template_expression_render_duration(
        self,
        render_path: str,
        duration_seconds: float,
    ) -> None:
        self._registry.track_template_expression_render_duration(
            render_path, duration_seconds
        )

    def track_variable_validation(self, result: str) -> None:
        self._registry.track_variable_validation(result)

    def track_variable_validation_failure(self, reason: str) -> None:
        self._registry.track_variable_validation_failure(reason)

    def track_environment_value_encryption(self) -> None:
        self._registry.track_environment_value_encryption()

    def track_environment_value_decryption(self) -> None:
        self._registry.track_environment_value_decryption()

    def track_environment_encryption_error(self, stage: str, reason: str) -> None:
        self._registry.track_environment_encryption_error(stage, reason)
