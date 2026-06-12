"""OpenTelemetry-backed metrics tracker implementing MetricsTrackerProtocol."""

from __future__ import annotations

from collections.abc import Iterator

from opentelemetry import metrics
from opentelemetry.metrics import Meter, Observation
from opentelemetry.sdk.metrics import MeterProvider

from pypost.core.metrics_registry import _normalize_new_tab_source
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.models.errors import ErrorCategory


class OtelMetricsTracker:
    """Records application metrics via OpenTelemetry instruments.

    Mirrors Prometheus metric names and labels from ``MetricsRegistry`` so operators can
    swap the default Prometheus tracker for OTel export without changing call sites.
    """

    def __init__(self, meter: Meter | None = None) -> None:
        self._meter = meter or metrics.get_meter(__name__)
        self._mcp_server_ready = 0
        self._init_instruments()
        self._meter.create_observable_gauge(
            "mcp_server_up",
            callbacks=[self._observe_mcp_server_up],
            description=(
                "Whether the MCP tool server has registered tools (1=ready, 0=idle)"
            ),
        )

    def _observe_mcp_server_up(self, options) -> Iterator[Observation]:
        yield Observation(self._mcp_server_ready)

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

    def track_gui_send_click(self) -> None:
        self._gui_send_clicks.add(1)

    def track_gui_save_action(self, source: str) -> None:
        self._gui_save_actions.add(1, {"source": source})

    def track_gui_save_as_action(self, source: str) -> None:
        self._gui_save_as_actions.add(1, {"source": source})

    def track_gui_new_tab_action(self, source: str) -> None:
        normalized = _normalize_new_tab_source(source)
        self._gui_new_tab_actions.add(1, {"source": normalized})

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

    def track_mcp_request_received(self, method: str) -> None:
        self._mcp_requests_received.add(1, {"method": method})

    def track_mcp_response_sent(self, method: str, status: str) -> None:
        self._mcp_responses_sent.add(1, {"method": method, "status": status})

    def set_mcp_server_up(self, ready: bool) -> None:
        self._mcp_server_ready = 1 if ready else 0

    def track_mcp_tool_call_duration(
        self, method: str, status: str, duration_seconds: float
    ) -> None:
        self._mcp_tool_call_duration_seconds.record(
            duration_seconds, {"method": method, "status": status}
        )

    def track_mcp_active_env_changed(self) -> None:
        self._mcp_active_env_changes.add(1)

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


def create_otel_metrics_tracker(
    meter_provider: MeterProvider | None = None,
    meter_name: str = "pypost",
) -> MetricsTrackerProtocol:
    """Build an OTel tracker, optionally installing a ``MeterProvider`` first."""
    if meter_provider is not None:
        metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter(meter_name)
    return OtelMetricsTracker(meter=meter)
