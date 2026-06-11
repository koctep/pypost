"""Metrics facade composing registry (counters) and server (uvicorn/MCP)."""

from PySide6.QtCore import QObject, Signal

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import MetricsServer
from pypost.models.errors import ErrorCategory


class MetricsManager(QObject):
    """Facade for Prometheus counters and the observability HTTP/MCP server."""

    start_failed = Signal(str)  # operator-facing bind / startup error

    def __init__(self) -> None:
        super().__init__()
        self._registry = MetricsRegistry()
        self._server = MetricsServer(self._registry)
        self._pending_start_failure: str | None = None
        self._start_failed_connected = False
        self._server.set_start_failed_handler(self._handle_start_failed)

    def _handle_start_failed(self, message: str) -> None:
        if self._start_failed_connected:
            self.start_failed.emit(message)
            return
        self._pending_start_failure = message

    def connect_start_failed(self, slot) -> None:
        """Connect UI slot and replay a failure that occurred before connect."""
        self.start_failed.connect(slot)
        self._start_failed_connected = True
        pending = self._pending_start_failure
        if pending is not None:
            self._pending_start_failure = None
            slot(pending)

    @property
    def registry(self):
        return self._registry.registry

    def start_server(self, host: str, port: int) -> None:
        self._server.start_server(host, port)

    def stop_server(self) -> None:
        self._server.stop_server()

    def restart_server(self, host: str, port: int) -> None:
        self._server.restart_server(host, port)

    async def list_resources(self):
        return await self._server.list_resources()

    async def read_resource(self, uri: str):
        return await self._server.read_resource(uri)

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

    def track_mcp_request_received(self, method: str) -> None:
        self._registry.track_mcp_request_received(method)

    def track_mcp_response_sent(self, method: str, status: str) -> None:
        self._registry.track_mcp_response_sent(method, status)

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
