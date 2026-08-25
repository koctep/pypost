"""Unit tests for MetricsManager Prometheus counter tracking (PYPOST-79)."""

import pytest

import asyncio
import unittest

from prometheus_client import generate_latest

from pypost.core.qt.metrics import MetricsManager
from pypost.models.errors import ErrorCategory

pytestmark = pytest.mark.timeout(30)


def _scrape(mm: MetricsManager) -> str:
    return generate_latest(mm.registry).decode("utf-8")


class TestMetricsManagerHttpTracking(unittest.TestCase):
    def test_track_request_sent(self):
        mm = MetricsManager()
        mm.track_request_sent("POST")
        mm.track_request_sent("POST")
        out = _scrape(mm)
        self.assertIn('requests_sent_total{method="POST"} 2.0', out)

    def test_track_response_received(self):
        mm = MetricsManager()
        mm.track_response_received("GET", "201")
        out = _scrape(mm)
        self.assertIn(
            'responses_received_total{method="GET",status_code="201"} 1.0',
            out,
        )


class TestMetricsManagerGuiTracking(unittest.TestCase):
    def test_track_gui_send_click(self):
        mm = MetricsManager()
        mm.track_gui_send_click()
        out = _scrape(mm)
        self.assertIn("gui_send_clicks_total 1.0", out)

    def test_track_gui_save_action_labeled(self):
        mm = MetricsManager()
        mm.track_gui_save_action("toolbar")
        out = _scrape(mm)
        self.assertIn('gui_save_actions_total{source="toolbar"} 1.0', out)

    def test_track_gui_response_search_action_boolean_label(self):
        mm = MetricsManager()
        mm.track_gui_response_search_action("shortcut", True)
        out = _scrape(mm)
        self.assertIn(
            'gui_response_search_actions_total{has_matches="true",source="shortcut"} 1.0',
            out,
        )

    def test_track_gui_new_tab_action_known_sources(self):
        mm = MetricsManager()
        mm.track_gui_new_tab_action("plus_button")
        mm.track_gui_new_tab_action("shortcut")
        out = _scrape(mm)
        self.assertIn(
            'gui_new_tab_actions_total{protocol="unknown",source="plus_button"} 1.0',
            out,
        )
        self.assertIn(
            'gui_new_tab_actions_total{protocol="unknown",source="shortcut"} 1.0',
            out,
        )

    def test_track_gui_new_tab_action_collections_context(self):
        mm = MetricsManager()
        mm.track_gui_new_tab_action("collections_context")
        out = _scrape(mm)
        self.assertIn(
            'gui_new_tab_actions_total{protocol="unknown",source="collections_context"} 1.0',
            out,
        )

    def test_track_gui_new_tab_action_invalid_source_maps_to_unknown(self):
        mm = MetricsManager()
        mm.track_gui_new_tab_action("test_source")
        out = _scrape(mm)
        self.assertIn(
            'gui_new_tab_actions_total{protocol="unknown",source="unknown"} 1.0',
            out,
        )
        self.assertNotIn('source="test_source"', out)

    def test_track_gui_new_tab_action_records_protocol(self):
        mm = MetricsManager()
        mm.track_gui_new_tab_action("shortcut", protocol="http")
        mm.track_gui_new_tab_action("plus_button", protocol="websocket")
        out = _scrape(mm)
        self.assertIn(
            'gui_new_tab_actions_total{protocol="http",source="shortcut"} 1.0',
            out,
        )
        self.assertIn(
            'gui_new_tab_actions_total{protocol="websocket",source="plus_button"} 1.0',
            out,
        )

    def test_track_gui_method_body_autoswitch(self):
        mm = MetricsManager()
        mm.track_gui_method_body_autoswitch("POST")
        out = _scrape(mm)
        self.assertIn('gui_method_body_autoswitches_total{method="POST"} 1.0', out)


class TestMetricsManagerHistoryAndErrors(unittest.TestCase):
    def test_track_history_entry_appended(self):
        mm = MetricsManager()
        mm.track_history_entry_appended("DELETE")
        out = _scrape(mm)
        self.assertIn('history_entries_appended_total{method="DELETE"} 1.0', out)

    def test_track_history_load_into_editor(self):
        mm = MetricsManager()
        mm.track_history_load_into_editor()
        out = _scrape(mm)
        self.assertIn("history_entries_loaded_into_editor_total 1.0", out)

    def test_track_history_record_error(self):
        mm = MetricsManager()
        mm.track_history_record_error()
        out = _scrape(mm)
        self.assertIn("history_record_errors_total 1.0", out)

    def test_track_request_error_uses_category_value(self):
        mm = MetricsManager()
        mm.track_request_error(ErrorCategory.TIMEOUT)
        out = _scrape(mm)
        self.assertIn('request_errors_total{category="timeout"} 1.0', out)

    def test_track_yaml_to_json_conversion_failed(self):
        mm = MetricsManager()
        mm.track_yaml_to_json_conversion_failed()
        out = _scrape(mm)
        self.assertIn("yaml_to_json_conversion_failed_total 1.0", out)


class TestMetricsManagerRetryExhaustion(unittest.TestCase):
    def test_track_retry_attempt_uppercases_method(self):
        mm = MetricsManager()
        mm.track_retry_attempt("post", "timeout")
        out = _scrape(mm)
        self.assertIn(
            'request_retries_total{method="POST",status_category="timeout"} 1.0',
            out,
        )

    def test_track_request_retry_exhaustion(self):
        mm = MetricsManager()
        mm.track_request_retry_exhaustion("https://api.example/x")
        out = _scrape(mm)
        self.assertIn(
            'request_retry_exhaustions_total{endpoint="https://api.example/x"} 1.0',
            out,
        )

    def test_track_mcp_server_up_and_tool_call_duration(self):
        mm = MetricsManager()
        mm.set_mcp_server_up(True)
        mm.track_mcp_tool_call_duration("GET", "success", 0.05)
        out = _scrape(mm)
        self.assertIn("mcp_server_up 1.0", out)
        self.assertIn(
            'mcp_tool_call_duration_seconds_count{method="GET",status="success"} 1.0',
            out,
        )

    def test_track_mcp_param_default_applied(self):
        mm = MetricsManager()
        mm.track_mcp_param_default_applied("GET")
        mm.track_mcp_param_default_applied("GET")
        out = _scrape(mm)
        self.assertIn('mcp_param_defaults_applied_total{method="GET"} 2.0', out)

    def test_mcp_server_instance_counts_are_aggregate_and_identity_free(self):
        mm = MetricsManager()
        mm.set_mcp_server_instance_counts(
            {"stopped": 1, "starting": 1, "running": 2, "failed": 3}
        )
        out = _scrape(mm)
        self.assertIn('mcp_server_instances{state="stopped"} 1.0', out)
        self.assertIn('mcp_server_instances{state="starting"} 1.0', out)
        self.assertIn('mcp_server_instances{state="running"} 2.0', out)
        self.assertIn('mcp_server_instances{state="failed"} 3.0', out)
        self.assertIn("mcp_server_up 1.0", out)

    def test_track_template_expression_render_duration(self):
        mm = MetricsManager()
        mm.track_template_expression_render_duration("runtime", 0.001)
        out = _scrape(mm)
        self.assertIn(
            'template_expression_render_duration_seconds_count{render_path="runtime"} 1.0',
            out,
        )


class TestMetricsManagerMcpResource(unittest.TestCase):
    def test_read_resource_metrics_success(self):
        mm = MetricsManager()

        async def _run():
            await mm.read_resource("metrics://all")

        asyncio.run(_run())
        out = _scrape(mm)
        self.assertIn(
            'mcp_requests_received_total{method="read_resource:metrics"} 1.0',
            out,
        )
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="success"} 1.0',
            out,
        )


if __name__ == "__main__":
    unittest.main()
