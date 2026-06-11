"""Prometheus counter registry and tracking methods (no I/O)."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from pypost.models.errors import ErrorCategory

_NEW_TAB_ACTION_SOURCES = frozenset(
    {"plus_button", "shortcut", "unknown", "collections_context"}
)


def _normalize_new_tab_source(source: str) -> str:
    if source in _NEW_TAB_ACTION_SOURCES:
        return source
    return "unknown"


class MetricsRegistry:
    """Owns Prometheus counters and pure tracking methods."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize all Prometheus metrics."""
        self.gui_send_clicks = Counter(
            "gui_send_clicks_total",
            "Number of times Send button was clicked",
            registry=self.registry,
        )

        self.gui_save_actions = Counter(
            "gui_save_actions_total",
            "Number of times Save action was triggered in GUI",
            ["source"],
            registry=self.registry,
        )
        self.gui_save_as_actions = Counter(
            "gui_save_as_actions_total",
            "Number of times Save As action was triggered in GUI",
            ["source"],
            registry=self.registry,
        )
        self.gui_new_tab_actions = Counter(
            "gui_new_tab_actions_total",
            "Number of times New Tab action was triggered in GUI",
            ["source"],
            registry=self.registry,
        )
        self.gui_copy_curl_actions = Counter(
            "gui_copy_curl_actions_total",
            "Number of times Copy cURL action was triggered in GUI",
            registry=self.registry,
        )
        self.gui_collection_delete_actions = Counter(
            "gui_collection_delete_actions_total",
            "Number of delete actions from collection context menu",
            ["item_type", "status"],
            registry=self.registry,
        )
        self.gui_collection_rename_actions = Counter(
            "gui_collection_rename_actions_total",
            "Number of rename actions from collection context menu",
            ["item_type", "status"],
            registry=self.registry,
        )

        self.gui_response_search_actions = Counter(
            "gui_response_search_actions_total",
            "Number of response body search actions",
            ["source", "has_matches"],
            registry=self.registry,
        )

        self.gui_variable_validation_total = Counter(
            "gui_variable_validation_total",
            "Number of variable name validation attempts",
            ["result"],
            registry=self.registry,
        )

        self.gui_variable_validation_failures_total = Counter(
            "gui_variable_validation_failures_total",
            "Number of failed variable name validations",
            ["reason"],
            registry=self.registry,
        )

        self.gui_method_body_autoswitches = Counter(
            "gui_method_body_autoswitches_total",
            "Number of times the Body tab was auto-selected due to method change",
            ["method"],
            registry=self.registry,
        )

        self.requests_sent = Counter(
            "requests_sent_total",
            "Number of HTTP requests sent",
            ["method"],
            registry=self.registry,
        )

        self.responses_received = Counter(
            "responses_received_total",
            "Number of HTTP responses received",
            ["method", "status_code"],
            registry=self.registry,
        )

        self.mcp_requests_received = Counter(
            "mcp_requests_received_total",
            "Number of requests received by MCP server",
            ["method"],
            registry=self.registry,
        )

        self.mcp_responses_sent = Counter(
            "mcp_responses_sent_total",
            "Number of responses sent by MCP server",
            ["method", "status"],
            registry=self.registry,
        )

        self.mcp_server_up = Gauge(
            "mcp_server_up",
            "Whether the MCP tool server has registered tools (1=ready, 0=idle)",
            registry=self.registry,
        )

        self.mcp_tool_call_duration_seconds = Histogram(
            "mcp_tool_call_duration_seconds",
            "MCP tool call execution duration in seconds",
            ["method", "status"],
            registry=self.registry,
        )

        self.mcp_active_env_changes = Counter(
            "mcp_active_env_changes_total",
            "Active environment changed while MCP server was running",
            registry=self.registry,
        )

        self.history_entries_appended = Counter(
            "history_entries_appended_total",
            "Number of request history entries recorded",
            ["method"],
            registry=self.registry,
        )
        self.history_entries_loaded_into_editor = Counter(
            "history_entries_loaded_into_editor_total",
            "Number of history entries loaded into the request editor",
            registry=self.registry,
        )

        self.request_errors = Counter(
            "request_errors_total",
            "Number of request execution errors by category",
            ["category"],
            registry=self.registry,
        )

        self.yaml_to_json_conversion_failed = Counter(
            "yaml_to_json_conversion_failed_total",
            "Number of YAML-to-JSON body conversion failures at send time",
            registry=self.registry,
        )

        self.history_record_errors = Counter(
            "history_record_errors_total",
            "Number of history recording failures",
            registry=self.registry,
        )
        self.hidden_value_masks_applied = Counter(
            "hidden_value_masks_applied_total",
            "Number of hidden-variable masking operations applied",
            ["surface"],
            registry=self.registry,
        )

        self._request_retries_total = Counter(
            "request_retries_total",
            "Number of retry attempts made",
            ["method", "status_category"],
            registry=self.registry,
        )
        self._request_retry_exhaustions_total = Counter(
            "request_retry_exhaustions_total",
            "Outbound HTTP requests where all configured retries were exhausted",
            ["endpoint"],
            registry=self.registry,
        )
        self.template_expression_render_attempts = Counter(
            "template_expression_render_attempts_total",
            "TemplateService render attempts for function placeholders in {{...}}",
            ["render_path", "outcome"],
            registry=self.registry,
        )
        self.template_expression_validation_failures = Counter(
            "template_expression_validation_failures_total",
            "TemplateService function-placeholder validation failures",
            ["render_path", "code", "function_name"],
            registry=self.registry,
        )
        self.environment_value_encryptions_total = Counter(
            "environment_value_encryptions_total",
            "Number of environment values encrypted before persistence",
            registry=self.registry,
        )
        self.environment_value_decryptions_total = Counter(
            "environment_value_decryptions_total",
            "Number of environment values decrypted during load",
            registry=self.registry,
        )
        self.environment_encryption_errors_total = Counter(
            "environment_encryption_errors_total",
            "Number of encryption/decryption errors in environment storage flow",
            ["stage", "reason"],
            registry=self.registry,
        )

    def track_gui_send_click(self) -> None:
        self.gui_send_clicks.inc()

    def track_gui_save_action(self, source: str) -> None:
        self.gui_save_actions.labels(source=source).inc()

    def track_gui_save_as_action(self, source: str) -> None:
        self.gui_save_as_actions.labels(source=source).inc()

    def track_gui_new_tab_action(self, source: str) -> None:
        normalized = _normalize_new_tab_source(source)
        self.gui_new_tab_actions.labels(source=normalized).inc()

    def track_gui_copy_curl_action(self) -> None:
        self.gui_copy_curl_actions.inc()

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None:
        self.gui_collection_delete_actions.labels(item_type=item_type, status=status).inc()

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None:
        self.gui_collection_rename_actions.labels(item_type=item_type, status=status).inc()

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None:
        self.gui_response_search_actions.labels(
            source=source, has_matches=str(has_matches).lower()
        ).inc()

    def track_gui_method_body_autoswitch(self, method: str) -> None:
        self.gui_method_body_autoswitches.labels(method=method).inc()

    def track_request_sent(self, method: str) -> None:
        self.requests_sent.labels(method=method).inc()

    def track_response_received(self, method: str, status_code: str) -> None:
        self.responses_received.labels(method=method, status_code=status_code).inc()

    def track_mcp_request_received(self, method: str) -> None:
        self.mcp_requests_received.labels(method=method).inc()

    def track_mcp_response_sent(self, method: str, status: str) -> None:
        self.mcp_responses_sent.labels(method=method, status=status).inc()

    def set_mcp_server_up(self, ready: bool) -> None:
        self.mcp_server_up.set(1 if ready else 0)

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None:
        self.mcp_tool_call_duration_seconds.labels(
            method=method, status=status
        ).observe(duration_seconds)

    def track_mcp_active_env_changed(self) -> None:
        self.mcp_active_env_changes.inc()

    def track_history_entry_appended(self, method: str) -> None:
        self.history_entries_appended.labels(method=method).inc()

    def track_history_load_into_editor(self) -> None:
        self.history_entries_loaded_into_editor.inc()

    def track_request_error(self, category: ErrorCategory) -> None:
        self.request_errors.labels(category=category.value).inc()

    def track_yaml_to_json_conversion_failed(self) -> None:
        self.yaml_to_json_conversion_failed.inc()

    def track_history_record_error(self) -> None:
        self.history_record_errors.inc()

    def track_hidden_value_mask_applied(self, surface: str) -> None:
        self.hidden_value_masks_applied.labels(surface=surface).inc()

    def track_retry_attempt(self, method: str, status_category: str) -> None:
        self._request_retries_total.labels(
            method=method.upper(), status_category=status_category
        ).inc()

    def track_request_retry_exhaustion(self, endpoint: str) -> None:
        self._request_retry_exhaustions_total.labels(endpoint=endpoint).inc()

    def track_template_expression_render_attempt(
        self,
        render_path: str,
        outcome: str,
    ) -> None:
        self.template_expression_render_attempts.labels(
            render_path=render_path,
            outcome=outcome,
        ).inc()

    def track_template_expression_validation_failure(
        self,
        render_path: str,
        code: str,
        function_name: str | None = None,
    ) -> None:
        self.template_expression_validation_failures.labels(
            render_path=render_path,
            code=code,
            function_name=function_name or "n/a",
        ).inc()

    def track_variable_validation(self, result: str) -> None:
        """Track variable name validation attempt.

        Args:
            result: Either "valid" or "invalid"
        """
        self.gui_variable_validation_total.labels(result=result).inc()

    def track_variable_validation_failure(self, reason: str) -> None:
        """Track failed variable name validation.

        Args:
            reason: Reason for failure ("empty", "starts_with_digit", "invalid_chars")
        """
        self.gui_variable_validation_failures_total.labels(reason=reason).inc()

    def track_environment_value_encryption(self) -> None:
        self.environment_value_encryptions_total.inc()

    def track_environment_value_decryption(self) -> None:
        self.environment_value_decryptions_total.inc()

    def track_environment_encryption_error(self, stage: str, reason: str) -> None:
        self.environment_encryption_errors_total.labels(
            stage=stage,
            reason=reason,
        ).inc()
