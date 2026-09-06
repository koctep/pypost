"""Prometheus counter registry and tracking methods (no I/O)."""
from __future__ import annotations

from collections.abc import Mapping

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from pypost.models.errors import ErrorCategory

_NEW_TAB_ACTION_SOURCES = frozenset(
    {"plus_button", "shortcut", "unknown", "collections_context", "last_tab"}
)
_NEW_TAB_PROTOCOLS = frozenset({"http", "websocket", "mcp_client", "unknown"})
_MCP_VALIDATION_STAGES = frozenset({"preflight", "execution_boundary", "unknown"})
_MCP_VALIDATION_TRANSPORTS = frozenset({"http", "websocket", "unknown"})
_MCP_VALIDATION_TYPES = frozenset(
    {"string", "integer", "integer_or_string", "number", "boolean", "array", "object", "unknown"}
)
_MCP_LIBRARY_DISCOVERY_OPERATIONS = frozenset({"libraries", "collections"})
_MCP_LIBRARY_DISCOVERY_OUTCOMES = frozenset({"success", "failure", "cancelled"})
_MCP_LIBRARY_VALIDATION_CATEGORIES = frozenset(
    {
        "library_invalid", "manifest_invalid", "collection_missing",
        "profile_missing", "profile_invalid", "success",
    }
)
_MCP_LIBRARY_SAVE_OUTCOMES = frozenset(
    {"commit", "rollback", "persistence_failure", "rollback_failure"}
)
_LIFECYCLE_OWNERS = frozenset(
    {
        "main_window",
        "tabs_presenter",
        "request_tab",
        "history_panel",
        "history_manager",
        "environment_storage_gateway",
        "env_presenter",
    }
)
_LIFECYCLE_OUTCOMES = frozenset({"success", "incomplete", "failed"})
_LIFECYCLE_EVENTS = frozenset(
    {"cancellation_requested", "admission_rejected", "late_signal_suppressed"}
)
_ENVIRONMENT_DISPOSITIONS = frozenset(
    {
        "persisted",
        "coalesced_into_newer_save",
        "failed",
        "incomplete",
        "rejected_after_cutoff",
    }
)
_HISTORY_IO_OPERATIONS = frozenset({"load", "save"})
_LIBRARY_OPERATIONS = frozenset(
    {
        "refresh",
        "check_dirty",
        "pull",
        "commit",
        "push",
        "commit_and_push",
        "switch_branch",
        "list_branches",
        "clone",
        "connect",
        "disconnect",
        "delete",
        "collection_import_file",
        "collection_import_library",
        "collection_import_refresh",
    }
)
_LIBRARY_OPERATION_OUTCOMES = frozenset(
    {"started", "success", "failure", "blocked", "rejected"}
)


def _normalize_new_tab_source(source: str) -> str:
    if source in _NEW_TAB_ACTION_SOURCES:
        return source
    return "unknown"


def _normalize_new_tab_protocol(protocol: str) -> str:
    if protocol in _NEW_TAB_PROTOCOLS:
        return protocol
    return "unknown"


def _normalize_mcp_validation_label(value: str, allowed: frozenset[str]) -> str:
    return value if value in allowed else "unknown"


def _normalize_lifecycle_label(value: str, allowed: frozenset[str]) -> str:
    return value if value in allowed else "unknown"


def _normalize_library_label(value: str, allowed: frozenset[str]) -> str:
    return value if value in allowed else "unknown"


class MetricsRegistry:
    """Owns Prometheus counters and pure tracking methods."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize all Prometheus metrics."""
        self._init_gui_metrics()
        self._init_http_metrics()
        self._init_mcp_metrics()
        self._init_encryption_metrics()
        self._init_websocket_metrics()
        self._init_lifecycle_metrics()

    def _init_lifecycle_metrics(self) -> None:
        """Register bounded presenter shutdown and admission metrics."""
        self.lifecycle_teardowns = Counter(
            "lifecycle_teardowns_total",
            "Completed bounded lifecycle teardown attempts",
            ["owner", "outcome"],
            registry=self.registry,
        )
        self.lifecycle_teardown_duration_seconds = Histogram(
            "lifecycle_teardown_duration_seconds",
            "Duration of bounded lifecycle teardown attempts",
            ["owner", "outcome"],
            registry=self.registry,
        )
        self.lifecycle_teardown_active_workers = Gauge(
            "lifecycle_teardown_active_workers",
            "Active workers observed when lifecycle teardown began",
            ["owner"],
            registry=self.registry,
        )
        self.lifecycle_teardown_pending_work = Gauge(
            "lifecycle_teardown_pending_work",
            "Pending work observed when lifecycle teardown began",
            ["owner"],
            registry=self.registry,
        )
        self.lifecycle_events = Counter(
            "lifecycle_events_total",
            "Lifecycle admission, cancellation, and late-delivery events",
            ["owner", "event"],
            registry=self.registry,
        )
        self.environment_update_dispositions = Counter(
            "environment_update_dispositions_total",
            "Terminal dispositions of accepted environment updates",
            ["disposition"],
            registry=self.registry,
        )
        self.history_io_failures = Counter(
            "history_io_failures_total",
            "History load and save failures",
            ["operation"],
            registry=self.registry,
        )

    def _init_gui_metrics(self) -> None:
        """Register GUI interaction counters."""
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
            ["source", "protocol"],
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
        self.gui_library_operations = Counter(
            "gui_library_operations_total",
            "Library Manager operations by bounded operation and outcome",
            ["operation", "outcome"],
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

        self.gui_variable_autocomplete_triggers = Counter(
            "gui_variable_autocomplete_triggers_total",
            "Number of variable autocomplete popup triggers",
            ["context"], registry=self.registry,
        )
        self.gui_variable_autocomplete_selections = Counter(
            "gui_variable_autocomplete_selections_total",
            "Number of variable autocomplete selections",
            ["context"], registry=self.registry,
        )
        self.gui_variable_autocomplete_feedback = Counter(
            "gui_variable_autocomplete_feedback_total",
            "Number of variable autocomplete feedback states",
            ["context", "status"], registry=self.registry,
        )
        self.gui_variable_autocomplete_environment_refreshes = Counter(
            "gui_variable_autocomplete_environment_refreshes_total",
            "Number of variable autocomplete environment refreshes",
            ["context"], registry=self.registry,
        )

    def _init_http_metrics(self) -> None:
        """Register HTTP request, history, and template counters."""
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

        self.response_body_truncated = Counter(
            "response_body_truncated_total",
            "Number of HTTP responses truncated due to max_response_bytes",
            ["method"],
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
        self.template_expression_render_duration_seconds = Histogram(
            "template_expression_render_duration_seconds",
            "TemplateService Jinja render duration in seconds",
            ["render_path"],
            registry=self.registry,
        )

    def _init_mcp_metrics(self) -> None:
        """Register MCP server counters, gauge, and histogram."""
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
        self.mcp_argument_validation_failures = Counter(
            "mcp_argument_validation_failures_total",
            "Number of MCP argument validation failures",
            ["stage", "transport", "declared_type"],
            registry=self.registry,
        )

        self.mcp_server_up = Gauge(
            "mcp_server_up",
            "Whether the MCP tool server has registered tools (1=ready, 0=idle)",
            registry=self.registry,
        )
        self.mcp_server_instances = Gauge(
            "mcp_server_instances",
            "Number of configured MCP server instances by lifecycle state",
            ["state"],
            registry=self.registry,
        )

        self.mcp_tool_call_duration_seconds = Histogram(
            "mcp_tool_call_duration_seconds",
            "MCP tool call execution duration in seconds",
            ["method", "status"],
            registry=self.registry,
        )

        self.mcp_library_discovery_total = Counter(
            "mcp_library_discovery_total",
            "Connected library and collection discovery outcomes",
            ["operation", "outcome"],
            registry=self.registry,
        )
        self.mcp_library_discovery_duration_seconds = Histogram(
            "mcp_library_discovery_duration_seconds",
            "Connected library and collection discovery duration",
            ["operation", "outcome"],
            registry=self.registry,
        )
        self.mcp_library_discovery_items = Histogram(
            "mcp_library_discovery_items",
            "Number of non-sensitive items returned by library discovery",
            ["operation"],
            registry=self.registry,
        )
        self.mcp_library_validation_failures = Counter(
            "mcp_library_validation_total",
            "Library-backed MCP runtime validation outcomes by safe category",
            ["category"],
            registry=self.registry,
        )
        self.mcp_library_save_outcomes = Counter(
            "mcp_library_save_outcomes_total",
            "Library-backed MCP save commit and rollback outcomes",
            ["outcome"],
            registry=self.registry,
        )
        self.mcp_library_save_duration_seconds = Histogram(
            "mcp_library_save_duration_seconds",
            "Library-backed MCP save duration by outcome",
            ["outcome"],
            registry=self.registry,
        )

        self.mcp_active_env_changes = Counter(
            "mcp_active_env_changes_total",
            "Active environment changed while MCP server was running",
            registry=self.registry,
        )

        self.mcp_param_defaults_applied = Counter(
            "mcp_param_defaults_applied_total",
            "Number of optional MCP tool params filled from their declared default "
            "because the caller omitted them",
            ["method"],
            registry=self.registry,
        )
        self.mcp_client_connect = Counter(
            "mcp_client_connect_total",
            "Outbound MCP Client Connect outcomes (not inbound MCP server traffic)",
            ["result"],
            registry=self.registry,
        )
        self.mcp_client_list_tools = Counter(
            "mcp_client_list_tools_total",
            "Outbound MCP Client list_tools outcomes by Connect or Refresh",
            ["result", "operation"],
            registry=self.registry,
        )
        self.mcp_client_call_tool = Counter(
            "mcp_client_call_tool_total",
            "Outbound MCP Client call_tool outcomes (not inbound MCP traffic)",
            ["result"],
            registry=self.registry,
        )

    def _init_encryption_metrics(self) -> None:
        """Register environment encryption counters."""
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

    def track_gui_new_tab_action(
        self, source: str, protocol: str = "unknown"
    ) -> None:
        normalized = _normalize_new_tab_source(source)
        normalized_protocol = _normalize_new_tab_protocol(protocol)
        self.gui_new_tab_actions.labels(
            source=normalized, protocol=normalized_protocol
        ).inc()

    def track_gui_copy_curl_action(self) -> None:
        self.gui_copy_curl_actions.inc()

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None:
        self.gui_collection_delete_actions.labels(item_type=item_type, status=status).inc()

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None:
        self.gui_collection_rename_actions.labels(item_type=item_type, status=status).inc()

    def track_gui_library_operation(self, operation: str, outcome: str) -> None:
        self.gui_library_operations.labels(
            operation=_normalize_library_label(operation, _LIBRARY_OPERATIONS),
            outcome=_normalize_library_label(outcome, _LIBRARY_OPERATION_OUTCOMES),
        ).inc()

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None:
        self.gui_response_search_actions.labels(
            source=source, has_matches=str(has_matches).lower()
        ).inc()

    def track_gui_method_body_autoswitch(self, method: str) -> None:
        self.gui_method_body_autoswitches.labels(method=method).inc()

    def track_gui_variable_autocomplete_trigger(self, context: str) -> None:
        self.gui_variable_autocomplete_triggers.labels(context=context).inc()

    def track_gui_variable_autocomplete_selection(self, context: str) -> None:
        self.gui_variable_autocomplete_selections.labels(context=context).inc()

    def track_gui_variable_autocomplete_feedback(
        self, context: str, status: str
    ) -> None:
        self.gui_variable_autocomplete_feedback.labels(
            context=context, status=status
        ).inc()

    def track_gui_variable_autocomplete_environment_refresh(self, context: str) -> None:
        self.gui_variable_autocomplete_environment_refreshes.labels(
            context=context
        ).inc()

    def track_request_sent(self, method: str) -> None:
        self.requests_sent.labels(method=method).inc()

    def track_response_received(self, method: str, status_code: str) -> None:
        self.responses_received.labels(method=method, status_code=status_code).inc()

    def track_response_body_truncated(self, method: str) -> None:
        self.response_body_truncated.labels(method=method).inc()

    def track_mcp_request_received(self, method: str) -> None:
        self.mcp_requests_received.labels(method=method).inc()

    def track_mcp_response_sent(self, method: str, status: str) -> None:
        self.mcp_responses_sent.labels(method=method, status=status).inc()

    def track_mcp_argument_validation_failure(
        self, stage: str, transport: str, declared_type: str
    ) -> None:
        self.mcp_argument_validation_failures.labels(
            stage=_normalize_mcp_validation_label(stage, _MCP_VALIDATION_STAGES),
            transport=_normalize_mcp_validation_label(
                transport, _MCP_VALIDATION_TRANSPORTS
            ),
            declared_type=_normalize_mcp_validation_label(
                declared_type, _MCP_VALIDATION_TYPES
            ),
        ).inc()

    def set_mcp_server_up(self, ready: bool) -> None:
        self.mcp_server_up.set(1 if ready else 0)

    def set_mcp_server_instance_counts(self, counts: Mapping[str, int]) -> None:
        """Publish aggregate MCP endpoint state without identity-bearing labels."""
        for state in ("stopped", "starting", "running", "failed"):
            self.mcp_server_instances.labels(state=state).set(counts.get(state, 0))
        self.set_mcp_server_up(counts.get("running", 0) > 0)

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None:
        self.mcp_tool_call_duration_seconds.labels(
            method=method, status=status
        ).observe(duration_seconds)

    def track_mcp_library_discovery(
        self, operation: str, outcome: str, duration_seconds: float, item_count: int
    ) -> None:
        operation = _normalize_library_label(operation, _MCP_LIBRARY_DISCOVERY_OPERATIONS)
        outcome = _normalize_library_label(outcome, _MCP_LIBRARY_DISCOVERY_OUTCOMES)
        self.mcp_library_discovery_total.labels(operation=operation, outcome=outcome).inc()
        self.mcp_library_discovery_duration_seconds.labels(
            operation=operation, outcome=outcome
        ).observe(max(0.0, duration_seconds))
        self.mcp_library_discovery_items.labels(operation=operation).observe(max(0, item_count))

    def track_mcp_library_validation(self, category: str) -> None:
        self.mcp_library_validation_failures.labels(
            category=_normalize_library_label(category, _MCP_LIBRARY_VALIDATION_CATEGORIES)
        ).inc()

    def track_mcp_library_save(
        self, outcome: str, duration_seconds: float | None = None
    ) -> None:
        outcome = _normalize_library_label(outcome, _MCP_LIBRARY_SAVE_OUTCOMES)
        self.mcp_library_save_outcomes.labels(outcome=outcome).inc()
        if duration_seconds is not None:
            self.mcp_library_save_duration_seconds.labels(outcome=outcome).observe(
                max(0.0, duration_seconds)
            )

    def track_mcp_active_env_changed(self) -> None:
        self.mcp_active_env_changes.inc()

    def track_mcp_param_default_applied(self, method: str) -> None:
        self.mcp_param_defaults_applied.labels(method=method).inc()

    def track_mcp_client_connect(self, result: str) -> None:
        self.mcp_client_connect.labels(result=result).inc()

    def track_mcp_client_list_tools(self, result: str, operation: str) -> None:
        self.mcp_client_list_tools.labels(
            result=result,
            operation=operation,
        ).inc()

    def track_mcp_client_call_tool(self, result: str) -> None:
        self.mcp_client_call_tool.labels(result=result).inc()

    def track_history_entry_appended(self, method: str) -> None:
        self.history_entries_appended.labels(method=method).inc()

    def track_history_load_into_editor(self) -> None:
        self.history_entries_loaded_into_editor.inc()

    def track_lifecycle_teardown(
        self,
        owner: str,
        outcome: str,
        elapsed_seconds: float,
        active_count: int,
        pending_count: int,
    ) -> None:
        owner = _normalize_lifecycle_label(owner, _LIFECYCLE_OWNERS)
        outcome = _normalize_lifecycle_label(outcome, _LIFECYCLE_OUTCOMES)
        self.lifecycle_teardowns.labels(owner=owner, outcome=outcome).inc()
        self.lifecycle_teardown_duration_seconds.labels(
            owner=owner, outcome=outcome
        ).observe(max(0.0, elapsed_seconds))
        self.lifecycle_teardown_active_workers.labels(owner=owner).set(
            max(0, active_count)
        )
        self.lifecycle_teardown_pending_work.labels(owner=owner).set(
            max(0, pending_count)
        )

    def track_lifecycle_event(self, owner: str, event: str, count: int = 1) -> None:
        self.lifecycle_events.labels(
            owner=_normalize_lifecycle_label(owner, _LIFECYCLE_OWNERS),
            event=_normalize_lifecycle_label(event, _LIFECYCLE_EVENTS),
        ).inc(max(0, count))

    def track_environment_update_disposition(self, disposition: str) -> None:
        self.environment_update_dispositions.labels(
            disposition=_normalize_lifecycle_label(
                disposition, _ENVIRONMENT_DISPOSITIONS
            )
        ).inc()

    def track_history_io_failure(self, operation: str) -> None:
        self.history_io_failures.labels(
            operation=_normalize_lifecycle_label(operation, _HISTORY_IO_OPERATIONS)
        ).inc()

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

    def track_template_expression_render_duration(
        self,
        render_path: str,
        duration_seconds: float,
    ) -> None:
        self.template_expression_render_duration_seconds.labels(
            render_path=render_path,
        ).observe(duration_seconds)

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

    def _init_websocket_metrics(self) -> None:
        """Register WebSocket Prometheus counters, gauge, and histogram."""
        self.websocket_sessions_opened = Counter(
            "websocket_sessions_opened_total",
            "Number of WebSocket sessions opened",
            ["outcome"],
            registry=self.registry,
        )
        self.websocket_sessions_closed = Counter(
            "websocket_sessions_closed_total",
            "Number of WebSocket sessions closed",
            ["reason"],
            registry=self.registry,
        )
        self.websocket_messages = Counter(
            "websocket_messages_total",
            "Number of WebSocket messages transferred",
            ["direction", "kind"],
            registry=self.registry,
        )
        self.websocket_message_bytes = Counter(
            "websocket_message_bytes_total",
            "Total volume of WebSocket payload bytes transferred",
            ["direction"],
            registry=self.registry,
        )
        self.websocket_stream_entries_dropped = Counter(
            "websocket_stream_entries_dropped_total",
            "Number of WebSocket stream entries dropped due to buffer bounds",
            ["reason"],
            registry=self.registry,
        )
        self.websocket_reconnect_attempts = Counter(
            "websocket_reconnect_attempts_total",
            "Number of WebSocket automatic reconnect attempts",
            ["outcome"],
            registry=self.registry,
        )
        self.websocket_active_sessions = Gauge(
            "websocket_active_sessions",
            "Instantaneous number of active concurrent WebSocket sessions",
            registry=self.registry,
        )
        self.websocket_session_start_refused = Counter(
            "websocket_session_start_refused_total",
            "Number of WebSocket session start attempts refused by concurrency policy",
            ["reason"],
            registry=self.registry,
        )
        self.websocket_probe_duration_seconds = Histogram(
            "websocket_probe_duration_seconds",
            "Duration of MCP WebSocket probe executions in seconds",
            ["outcome"],
            registry=self.registry,
        )

    def track_environment_encryption_error(self, stage: str, reason: str) -> None:
        self.environment_encryption_errors_total.labels(
            stage=stage,
            reason=reason,
        ).inc()

    def track_websocket_session_opened(self, outcome: str) -> None:
        self.websocket_sessions_opened.labels(outcome=outcome).inc()

    def track_websocket_session_closed(self, reason: str) -> None:
        self.websocket_sessions_closed.labels(reason=reason).inc()

    def track_websocket_message(self, direction: str, kind: str) -> None:
        self.websocket_messages.labels(direction=direction, kind=kind).inc()

    def track_websocket_message_bytes(self, direction: str, byte_count: int) -> None:
        self.websocket_message_bytes.labels(direction=direction).inc(byte_count)

    def track_websocket_stream_entries_dropped(
        self, reason: str, count: int = 1
    ) -> None:
        self.websocket_stream_entries_dropped.labels(reason=reason).inc(count)

    def track_websocket_reconnect_attempt(self, outcome: str) -> None:
        self.websocket_reconnect_attempts.labels(outcome=outcome).inc()

    def set_websocket_active_sessions(self, count: int) -> None:
        self.websocket_active_sessions.set(count)

    def track_websocket_session_start_refused(self, reason: str) -> None:
        self.websocket_session_start_refused.labels(reason=reason).inc()

    def track_websocket_probe_duration(
        self, outcome: str, duration_seconds: float
    ) -> None:
        self.websocket_probe_duration_seconds.labels(outcome=outcome).observe(
            duration_seconds
        )
