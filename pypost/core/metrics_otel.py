"""OpenTelemetry-backed metrics tracker implementing MetricsTrackerProtocol."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

try:
    from opentelemetry import metrics
    from opentelemetry.metrics import Meter, Observation
    from opentelemetry.sdk.metrics import MeterProvider
except ImportError:  # pragma: no cover - exercised when dependency is absent.
    metrics = None  # type: ignore[assignment]
    Meter = Any  # type: ignore[assignment,misc]
    Observation = Any  # type: ignore[assignment,misc]
    MeterProvider = Any  # type: ignore[assignment,misc]

from pypost.core.metrics_registry import (
    _normalize_new_tab_protocol,
    _normalize_new_tab_source,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.models.errors import ErrorCategory


def _ensure_otel_available() -> None:
    if metrics is None:
        raise ImportError(
            "OpenTelemetry dependency is missing. Install the OTel extra "
            "(pip install -e '.[otel]' or make venv-otel) to use metrics_otel."
        )


class OtelMetricsTracker:
    """Records application metrics via OpenTelemetry instruments.

    Mirrors Prometheus metric names and labels from ``MetricsRegistry`` so operators can
    swap the default Prometheus tracker for OTel export without changing call sites.
    """

    def __init__(self, meter: Meter | None = None) -> None:
        _ensure_otel_available()
        self._meter = meter or metrics.get_meter(__name__)
        self._mcp_server_ready = 0
        self._mcp_server_instance_counts = {
            "stopped": 0,
            "starting": 0,
            "running": 0,
            "failed": 0,
        }
        self._init_instruments()
        self._meter.create_observable_gauge(
            "mcp_server_up",
            callbacks=[self._observe_mcp_server_up],
            description=(
                "Whether the MCP tool server has registered tools (1=ready, 0=idle)"
            ),
        )
        self._meter.create_observable_gauge(
            "mcp_server_instances",
            callbacks=[self._observe_mcp_server_instance_counts],
            description="Number of configured MCP server instances by lifecycle state",
        )
        self._websocket_active_sessions_count = 0
        self._meter.create_observable_gauge(
            "websocket_active_sessions",
            callbacks=[self._observe_websocket_active_sessions],
            description="Instantaneous number of active concurrent WebSocket sessions",
        )

    def _observe_mcp_server_up(self, options) -> Iterator[Observation]:
        yield Observation(self._mcp_server_ready)

    def _observe_mcp_server_instance_counts(self, options) -> Iterator[Observation]:
        for state, count in self._mcp_server_instance_counts.items():
            yield Observation(count, attributes={"state": state})

    def _observe_websocket_active_sessions(self, options) -> Iterator[Observation]:
        yield Observation(self._websocket_active_sessions_count)

    def _init_instruments(self) -> None:
        meter = self._meter
        self._gui_send_clicks = meter.create_counter(
            "gui_send_clicks_total",
            description="Number of times Send button was clicked",
        )
        self._gui_save_actions = meter.create_counter(
            "gui_save_actions_total",
            description="Number of times Save action was triggered in GUI",
        )
        self._gui_save_as_actions = meter.create_counter(
            "gui_save_as_actions_total",
            description="Number of times Save As action was triggered in GUI",
        )
        self._gui_new_tab_actions = meter.create_counter(
            "gui_new_tab_actions_total",
            description="Number of times New Tab action was triggered in GUI",
        )
        self._gui_copy_curl_actions = meter.create_counter(
            "gui_copy_curl_actions_total",
            description="Number of times Copy cURL action was triggered in GUI",
        )
        self._gui_collection_delete_actions = meter.create_counter(
            "gui_collection_delete_actions_total",
            description="Number of delete actions from collection context menu",
        )
        self._gui_collection_rename_actions = meter.create_counter(
            "gui_collection_rename_actions_total",
            description="Number of rename actions from collection context menu",
        )
        self._gui_response_search_actions = meter.create_counter(
            "gui_response_search_actions_total",
            description="Number of response body search actions",
        )
        self._gui_variable_validation_total = meter.create_counter(
            "gui_variable_validation_total",
            description="Number of variable name validation attempts",
        )
        self._gui_variable_validation_failures_total = meter.create_counter(
            "gui_variable_validation_failures_total",
            description="Number of failed variable name validations",
        )
        self._gui_method_body_autoswitches = meter.create_counter(
            "gui_method_body_autoswitches_total",
            description=(
                "Number of times the Body tab was auto-selected due to method change"
            ),
        )
        self._requests_sent = meter.create_counter(
            "requests_sent_total",
            description="Number of HTTP requests sent",
        )
        self._responses_received = meter.create_counter(
            "responses_received_total",
            description="Number of HTTP responses received",
        )
        self._response_body_truncated = meter.create_counter(
            "response_body_truncated_total",
            description="Number of HTTP responses truncated due to max_response_bytes",
        )
        self._mcp_requests_received = meter.create_counter(
            "mcp_requests_received_total",
            description="Number of requests received by MCP server",
        )
        self._mcp_responses_sent = meter.create_counter(
            "mcp_responses_sent_total",
            description="Number of responses sent by MCP server",
        )
        self._mcp_tool_call_duration_seconds = meter.create_histogram(
            "mcp_tool_call_duration_seconds",
            description="MCP tool call execution duration in seconds",
            unit="s",
        )
        self._mcp_active_env_changes = meter.create_counter(
            "mcp_active_env_changes_total",
            description="Active environment changed while MCP server was running",
        )
        self._mcp_param_defaults_applied = meter.create_counter(
            "mcp_param_defaults_applied_total",
            description=(
                "Number of optional MCP tool params filled from their declared "
                "default because the caller omitted them"
            ),
        )
        self._mcp_client_connect = meter.create_counter(
            "mcp_client_connect_total",
            description=(
                "Outbound MCP Client Connect outcomes "
                "(not inbound MCP server traffic)"
            ),
        )
        self._mcp_client_list_tools = meter.create_counter(
            "mcp_client_list_tools_total",
            description=(
                "Outbound MCP Client list_tools outcomes by Connect or Refresh"
            ),
        )
        self._history_entries_appended = meter.create_counter(
            "history_entries_appended_total",
            description="Number of request history entries recorded",
        )
        self._history_entries_loaded_into_editor = meter.create_counter(
            "history_entries_loaded_into_editor_total",
            description="Number of history entries loaded into the request editor",
        )
        self._request_errors = meter.create_counter(
            "request_errors_total",
            description="Number of request execution errors by category",
        )
        self._yaml_to_json_conversion_failed = meter.create_counter(
            "yaml_to_json_conversion_failed_total",
            description="Number of YAML-to-JSON body conversion failures at send time",
        )
        self._history_record_errors = meter.create_counter(
            "history_record_errors_total",
            description="Number of history recording failures",
        )
        self._hidden_value_masks_applied = meter.create_counter(
            "hidden_value_masks_applied_total",
            description="Number of hidden-variable masking operations applied",
        )
        self._request_retries_total = meter.create_counter(
            "request_retries_total",
            description="Number of retry attempts made",
        )
        self._request_retry_exhaustions_total = meter.create_counter(
            "request_retry_exhaustions_total",
            description=(
                "Outbound HTTP requests where all configured retries were exhausted"
            ),
        )
        self._template_expression_render_attempts = meter.create_counter(
            "template_expression_render_attempts_total",
            description=(
                "TemplateService render attempts for function placeholders in {{...}}"
            ),
        )
        self._template_expression_validation_failures = meter.create_counter(
            "template_expression_validation_failures_total",
            description="TemplateService function-placeholder validation failures",
        )
        self._template_expression_render_duration_seconds = meter.create_histogram(
            "template_expression_render_duration_seconds",
            description="TemplateService Jinja render duration in seconds",
            unit="s",
        )
        self._environment_value_encryptions_total = meter.create_counter(
            "environment_value_encryptions_total",
            description="Number of environment values encrypted before persistence",
        )
        self._environment_value_decryptions_total = meter.create_counter(
            "environment_value_decryptions_total",
            description="Number of environment values decrypted during load",
        )
        self._environment_encryption_errors_total = meter.create_counter(
            "environment_encryption_errors_total",
            description=(
                "Number of encryption/decryption errors in environment storage flow"
            ),
        )
        self._websocket_sessions_opened = meter.create_counter(
            "websocket_sessions_opened_total",
            description="Number of WebSocket sessions opened",
        )
        self._websocket_sessions_closed = meter.create_counter(
            "websocket_sessions_closed_total",
            description="Number of WebSocket sessions closed",
        )
        self._websocket_messages = meter.create_counter(
            "websocket_messages_total",
            description="Number of WebSocket messages transferred",
        )
        self._websocket_message_bytes = meter.create_counter(
            "websocket_message_bytes_total",
            description="Total volume of WebSocket payload bytes transferred",
        )
        self._websocket_stream_entries_dropped = meter.create_counter(
            "websocket_stream_entries_dropped_total",
            description="Number of WebSocket stream entries dropped due to buffer bounds",
        )
        self._websocket_reconnect_attempts = meter.create_counter(
            "websocket_reconnect_attempts_total",
            description="Number of WebSocket automatic reconnect attempts",
        )
        self._websocket_session_start_refused = meter.create_counter(
            "websocket_session_start_refused_total",
            description="Number of WebSocket session start attempts refused by concurrency policy",
        )
        self._websocket_probe_duration_seconds = meter.create_histogram(
            "websocket_probe_duration_seconds",
            description="Duration of MCP WebSocket probe executions in seconds",
            unit="s",
        )

    def track_gui_send_click(self) -> None:
        self._gui_send_clicks.add(1)

    def track_gui_save_action(self, source: str) -> None:
        self._gui_save_actions.add(1, {"source": source})

    def track_gui_save_as_action(self, source: str) -> None:
        self._gui_save_as_actions.add(1, {"source": source})

    def track_gui_new_tab_action(
        self, source: str, protocol: str = "unknown"
    ) -> None:
        normalized = _normalize_new_tab_source(source)
        normalized_protocol = _normalize_new_tab_protocol(protocol)
        self._gui_new_tab_actions.add(
            1, {"source": normalized, "protocol": normalized_protocol}
        )

    def track_gui_copy_curl_action(self) -> None:
        self._gui_copy_curl_actions.add(1)

    def track_gui_collection_delete_action(self, item_type: str, status: str) -> None:
        self._gui_collection_delete_actions.add(
            1, {"item_type": item_type, "status": status}
        )

    def track_gui_collection_rename_action(self, item_type: str, status: str) -> None:
        self._gui_collection_rename_actions.add(
            1, {"item_type": item_type, "status": status}
        )

    def track_gui_response_search_action(self, source: str, has_matches: bool) -> None:
        self._gui_response_search_actions.add(
            1,
            {"source": source, "has_matches": str(has_matches).lower()},
        )

    def track_gui_method_body_autoswitch(self, method: str) -> None:
        self._gui_method_body_autoswitches.add(1, {"method": method})

    def track_request_sent(self, method: str) -> None:
        self._requests_sent.add(1, {"method": method})

    def track_response_received(self, method: str, status_code: str) -> None:
        self._responses_received.add(
            1, {"method": method, "status_code": status_code}
        )

    def track_response_body_truncated(self, method: str) -> None:
        self._response_body_truncated.add(1, {"method": method})

    def track_mcp_request_received(self, method: str) -> None:
        self._mcp_requests_received.add(1, {"method": method})

    def track_mcp_response_sent(self, method: str, status: str) -> None:
        self._mcp_responses_sent.add(1, {"method": method, "status": status})

    def set_mcp_server_up(self, ready: bool) -> None:
        self._mcp_server_ready = 1 if ready else 0

    def set_mcp_server_instance_counts(self, counts: Mapping[str, int]) -> None:
        self._mcp_server_instance_counts = {
            state: counts.get(state, 0)
            for state in ("stopped", "starting", "running", "failed")
        }
        self.set_mcp_server_up(self._mcp_server_instance_counts["running"] > 0)

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None:
        self._mcp_tool_call_duration_seconds.record(
            duration_seconds, {"method": method, "status": status}
        )

    def track_mcp_active_env_changed(self) -> None:
        self._mcp_active_env_changes.add(1)

    def track_mcp_param_default_applied(self, method: str) -> None:
        self._mcp_param_defaults_applied.add(1, {"method": method})

    def track_mcp_client_connect(self, result: str) -> None:
        self._mcp_client_connect.add(1, {"result": result})

    def track_mcp_client_list_tools(self, result: str, operation: str) -> None:
        self._mcp_client_list_tools.add(
            1, {"result": result, "operation": operation}
        )

    def track_history_entry_appended(self, method: str) -> None:
        self._history_entries_appended.add(1, {"method": method})

    def track_history_load_into_editor(self) -> None:
        self._history_entries_loaded_into_editor.add(1)

    def track_request_error(self, category: ErrorCategory) -> None:
        self._request_errors.add(1, {"category": category.value})

    def track_yaml_to_json_conversion_failed(self) -> None:
        self._yaml_to_json_conversion_failed.add(1)

    def track_history_record_error(self) -> None:
        self._history_record_errors.add(1)

    def track_hidden_value_mask_applied(self, surface: str) -> None:
        self._hidden_value_masks_applied.add(1, {"surface": surface})

    def track_retry_attempt(self, method: str, status_category: str) -> None:
        self._request_retries_total.add(
            1, {"method": method.upper(), "status_category": status_category}
        )

    def track_request_retry_exhaustion(self, endpoint: str) -> None:
        self._request_retry_exhaustions_total.add(1, {"endpoint": endpoint})

    def track_template_expression_render_attempt(
        self,
        render_path: str,
        outcome: str,
    ) -> None:
        self._template_expression_render_attempts.add(
            1, {"render_path": render_path, "outcome": outcome}
        )

    def track_template_expression_validation_failure(
        self,
        render_path: str,
        code: str,
        function_name: str | None = None,
    ) -> None:
        self._template_expression_validation_failures.add(
            1,
            {
                "render_path": render_path,
                "code": code,
                "function_name": function_name or "n/a",
            },
        )

    def track_template_expression_render_duration(
        self,
        render_path: str,
        duration_seconds: float,
    ) -> None:
        self._template_expression_render_duration_seconds.record(
            duration_seconds,
            {"render_path": render_path},
        )

    def track_variable_validation(self, result: str) -> None:
        self._gui_variable_validation_total.add(1, {"result": result})

    def track_variable_validation_failure(self, reason: str) -> None:
        self._gui_variable_validation_failures_total.add(1, {"reason": reason})

    def track_environment_value_encryption(self) -> None:
        self._environment_value_encryptions_total.add(1)

    def track_environment_value_decryption(self) -> None:
        self._environment_value_decryptions_total.add(1)

    def track_environment_encryption_error(self, stage: str, reason: str) -> None:
        self._environment_encryption_errors_total.add(
            1, {"stage": stage, "reason": reason}
        )

    def track_websocket_session_opened(self, outcome: str) -> None:
        self._websocket_sessions_opened.add(1, {"outcome": outcome})

    def track_websocket_session_closed(self, reason: str) -> None:
        self._websocket_sessions_closed.add(1, {"reason": reason})

    def track_websocket_message(self, direction: str, kind: str) -> None:
        self._websocket_messages.add(1, {"direction": direction, "kind": kind})

    def track_websocket_message_bytes(self, direction: str, byte_count: int) -> None:
        self._websocket_message_bytes.add(byte_count, {"direction": direction})

    def track_websocket_stream_entries_dropped(
        self, reason: str, count: int = 1
    ) -> None:
        self._websocket_stream_entries_dropped.add(count, {"reason": reason})

    def track_websocket_reconnect_attempt(self, outcome: str) -> None:
        self._websocket_reconnect_attempts.add(1, {"outcome": outcome})

    def set_websocket_active_sessions(self, count: int) -> None:
        self._websocket_active_sessions_count = count

    def track_websocket_session_start_refused(self, reason: str) -> None:
        self._websocket_session_start_refused.add(1, {"reason": reason})

    def track_websocket_probe_duration(
        self, outcome: str, duration_seconds: float
    ) -> None:
        self._websocket_probe_duration_seconds.record(
            duration_seconds, {"outcome": outcome}
        )


def create_otel_metrics_tracker(
    meter_provider: MeterProvider | None = None,
    meter_name: str = "pypost",
) -> MetricsTrackerProtocol:
    """Build an OTel tracker, optionally installing a ``MeterProvider`` first."""
    _ensure_otel_available()
    if meter_provider is not None:
        metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter(meter_name)
    return OtelMetricsTracker(meter=meter)
