"""Unit tests for MetricsManager Prometheus counter tracking (PYPOST-79)."""

import asyncio
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from prometheus_client import generate_latest

from pypost.core.metrics import MetricsManager
from pypost.models.errors import ErrorCategory


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


class MetricsServerLifecycleTests(unittest.TestCase):
    """start_server on a live server must restart it, not deadlock.

    start_server holds server_lock while calling stop_server, which takes the
    same lock; a non-reentrant lock hangs the caller there forever.
    """

    @staticmethod
    def _fake_uvicorn(manager):
        """Stand in for _run_uvicorn: alive until stop_server asks it to exit."""
        def run(self):
            self.server_instance = SimpleNamespace(should_exit=False)
            while not self.server_instance.should_exit:
                time.sleep(0.01)
        return patch.object(type(manager), "_run_uvicorn", run)

    def _release_on_cleanup(self, manager):
        """Stop the fake server without taking server_lock.

        Cleaning up through stop_server would itself block on the lock the
        deadlock leaves held, turning a failed assertion into a hung suite.
        """
        def release():
            if manager.server_instance is not None:
                manager.server_instance.should_exit = True
        self.addCleanup(release)

    def test_start_on_a_live_server_does_not_deadlock(self):
        manager = MetricsManager()
        with self._fake_uvicorn(manager):
            manager.start_server("127.0.0.1", 9099)
            self._release_on_cleanup(manager)

            done = threading.Event()

            def restart():
                manager.start_server("127.0.0.1", 9100)
                done.set()

            worker = threading.Thread(target=restart, daemon=True)
            worker.start()

            self.assertTrue(
                done.wait(5), "start_server deadlocked against its own stop_server"
            )
            self.assertEqual(9100, manager._current_port)

    def test_restart_server_rebinds_the_new_port(self):
        manager = MetricsManager()
        with self._fake_uvicorn(manager):
            manager.start_server("127.0.0.1", 9099)
            self._release_on_cleanup(manager)

            manager.restart_server("127.0.0.1", 9101)

            self.assertEqual(9101, manager._current_port)
            self.assertTrue(manager.thread.is_alive())

