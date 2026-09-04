"""Unit tests for MetricsRegistry MCP counter tracking (PYPOST-177)."""

import pytest

import unittest

from prometheus_client import generate_latest

from pypost.core.metrics_registry import MetricsRegistry

pytestmark = pytest.mark.timeout(30)


def _scrape(registry: MetricsRegistry) -> str:
    return generate_latest(registry.registry).decode("utf-8")


class TestMetricsRegistryMcpCounters(unittest.TestCase):
    def test_track_mcp_request_received(self):
        reg = MetricsRegistry()
        reg.track_mcp_request_received("read_resource:metrics")
        reg.track_mcp_request_received("read_resource:metrics")
        out = _scrape(reg)
        self.assertIn(
            'mcp_requests_received_total{method="read_resource:metrics"} 2.0',
            out,
        )

    def test_track_mcp_response_sent_success(self):
        reg = MetricsRegistry()
        reg.track_mcp_response_sent("read_resource:metrics", "success")
        out = _scrape(reg)
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="success"} 1.0',
            out,
        )

    def test_track_mcp_response_sent_error(self):
        reg = MetricsRegistry()
        reg.track_mcp_response_sent("read_resource:metrics", "error")
        out = _scrape(reg)
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="error"} 1.0',
            out,
        )

    def test_track_mcp_active_env_changed(self):
        reg = MetricsRegistry()
        reg.track_mcp_active_env_changed()
        reg.track_mcp_active_env_changed()
        out = _scrape(reg)
        self.assertIn("mcp_active_env_changes_total 2.0", out)

    def test_track_mcp_param_default_applied(self):
        reg = MetricsRegistry()
        reg.track_mcp_param_default_applied("GET")
        reg.track_mcp_param_default_applied("GET")
        out = _scrape(reg)
        self.assertIn('mcp_param_defaults_applied_total{method="GET"} 2.0', out)

    def test_track_mcp_client_connect(self):
        reg = MetricsRegistry()
        reg.track_mcp_client_connect("success")
        reg.track_mcp_client_connect("error")
        out = _scrape(reg)
        self.assertIn('mcp_client_connect_total{result="success"} 1.0', out)
        self.assertIn('mcp_client_connect_total{result="error"} 1.0', out)
        self.assertNotIn("mcp_requests_received_total{", out)


class TestMetricsRegistryVariableAutocompleteCounters(unittest.TestCase):
    def test_track_variable_autocomplete_counters(self):
        reg = MetricsRegistry()
        reg.track_gui_variable_autocomplete_trigger("query")
        reg.track_gui_variable_autocomplete_selection("query")
        reg.track_gui_variable_autocomplete_feedback("body", "unavailable")
        reg.track_gui_variable_autocomplete_environment_refresh("header")

        out = _scrape(reg)
        self.assertIn(
            'gui_variable_autocomplete_triggers_total{context="query"} 1.0',
            out,
        )
        self.assertIn(
            'gui_variable_autocomplete_selections_total{context="query"} 1.0',
            out,
        )
        self.assertIn(
            'gui_variable_autocomplete_feedback_total{context="body",status="unavailable"} 1.0',
            out,
        )
        self.assertIn(
            'gui_variable_autocomplete_environment_refreshes_total{context="header"} 1.0',
            out,
        )


class TestMetricsRegistryMcpClientCounters(unittest.TestCase):
    def test_track_mcp_client_list_tools(self):
        reg = MetricsRegistry()
        reg.track_mcp_client_list_tools("success", "connect")
        reg.track_mcp_client_list_tools("error", "refresh")
        out = _scrape(reg)
        self.assertIn(
            'mcp_client_list_tools_total{operation="connect",result="success"} 1.0',
            out,
        )
        self.assertIn(
            'mcp_client_list_tools_total{operation="refresh",result="error"} 1.0',
            out,
        )

    def test_track_mcp_client_call_tool(self):
        reg = MetricsRegistry()
        reg.track_mcp_client_call_tool("success")
        reg.track_mcp_client_call_tool("error")
        out = _scrape(reg)
        self.assertIn('mcp_client_call_tool_total{result="success"} 1.0', out)
        self.assertIn('mcp_client_call_tool_total{result="error"} 1.0', out)
        self.assertNotIn("mcp_requests_received_total{", out)


class TestMetricsRegistryTemplateRenderDuration(unittest.TestCase):
    def test_track_template_expression_render_duration(self):
        reg = MetricsRegistry()
        reg.track_template_expression_render_duration("runtime", 0.001)
        reg.track_template_expression_render_duration("hover", 0.002)
        out = _scrape(reg)
        self.assertIn(
            'template_expression_render_duration_seconds_count{render_path="runtime"} 1.0',
            out,
        )
        self.assertIn(
            'template_expression_render_duration_seconds_count{render_path="hover"} 1.0',
            out,
        )


class TestMetricsRegistryLifecycle(unittest.TestCase):
    def test_track_lifecycle_teardown_records_outcome_duration_and_work(self):
        reg = MetricsRegistry()
        reg.track_lifecycle_teardown(
            "tabs_presenter", "incomplete", 0.25, active_count=2, pending_count=3
        )

        out = _scrape(reg)
        self.assertIn(
            'lifecycle_teardowns_total{outcome="incomplete",owner="tabs_presenter"} 1.0',
            out,
        )
        self.assertIn(
            'lifecycle_teardown_duration_seconds_count{outcome="incomplete",owner="tabs_presenter"} 1.0',
            out,
        )
        self.assertIn(
            'lifecycle_teardown_active_workers{owner="tabs_presenter"} 2.0',
            out,
        )
        self.assertIn(
            'lifecycle_teardown_pending_work{owner="tabs_presenter"} 3.0',
            out,
        )

    def test_track_lifecycle_events_and_outcomes_use_bounded_labels(self):
        reg = MetricsRegistry()
        reg.track_lifecycle_event("tabs_presenter", "late_signal_suppressed", 2)
        reg.track_environment_update_disposition("persisted")
        reg.track_history_io_failure("save")

        out = _scrape(reg)
        self.assertIn(
            'lifecycle_events_total{event="late_signal_suppressed",owner="tabs_presenter"} 2.0',
            out,
        )
        self.assertIn(
            'environment_update_dispositions_total{disposition="persisted"} 1.0',
            out,
        )
        self.assertIn('history_io_failures_total{operation="save"} 1.0', out)


if __name__ == "__main__":
    unittest.main()
