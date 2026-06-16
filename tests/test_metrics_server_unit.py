"""Pure unit tests for MetricsServer lifecycle (PYPOST-720, PYPOST-726)."""
import asyncio
import pytest
import unittest
import warnings
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.timeout(30)

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import MetricsServer


def _make_server() -> MetricsServer:
    return MetricsServer(MetricsRegistry())


class TestMetricsServerSetStartFailedHandler(unittest.TestCase):
    def test_pending_failure_delivered_when_handler_set_later(self):
        server = _make_server()
        server._pending_start_failure = "port busy"
        received: list[str] = []
        server.set_start_failed_handler(received.append)
        self.assertEqual(received, ["port busy"])
        self.assertIsNone(server._pending_start_failure)

    def test_no_pending_failure_handler_called_zero_times(self):
        server = _make_server()
        received: list[str] = []
        server.set_start_failed_handler(received.append)
        self.assertEqual(received, [])


class TestMetricsServerListResources(unittest.TestCase):
    def test_list_resources_returns_metrics_resource(self):
        server = _make_server()
        resources = asyncio.run(server.list_resources())
        self.assertEqual(len(resources), 1)
        self.assertEqual(str(resources[0].uri), "metrics://all")


class TestMetricsServerMcpReadResource(unittest.TestCase):
    def test_mcp_read_resource_unknown_uri_raises(self):
        server = _make_server()
        with self.assertRaises(ValueError):
            asyncio.run(server._mcp_read_resource("metrics://unknown"))

    def test_mcp_read_resource_valid_uri_returns_text(self):
        server = _make_server()
        result = asyncio.run(server._mcp_read_resource("metrics://all"))
        self.assertIsInstance(result, str)


class TestMetricsServerNotifyStarted(unittest.TestCase):
    def test_notify_started_idempotent_when_already_notified(self):
        server = _make_server()
        server._startup_notified = True
        with self.assertLogs("pypost.core.metrics_server", level="INFO") as cm:
            server._startup_notified = False
            server._notify_started()
        server._startup_notified = True
        # Second call should be a no-op — no additional log
        initial_count = len(cm.output)
        server._notify_started()
        self.assertEqual(len(cm.output), initial_count)

    def test_notify_started_noop_when_stop_event_set(self):
        server = _make_server()
        server._stop_event.set()
        # Should not raise and should not log
        server._notify_started()
        self.assertFalse(server._startup_notified)


class TestMetricsServerNotifyStartFailed(unittest.TestCase):
    def test_no_handler_stores_pending_failure(self):
        server = _make_server()
        server._start_failed_handler = None
        with self.assertLogs("pypost.core.metrics_server", level="ERROR"):
            server._notify_start_failed("port busy")
        self.assertEqual(server._pending_start_failure, "port busy")

    def test_with_handler_calls_handler(self):
        server = _make_server()
        received: list[str] = []
        server._start_failed_handler = received.append
        with self.assertLogs("pypost.core.metrics_server", level="ERROR"):
            server._notify_start_failed("port busy")
        self.assertEqual(received, ["port busy"])
        self.assertIsNone(server._pending_start_failure)


class TestMetricsServerRunUvicornUnit(unittest.TestCase):
    def test_generic_exception_calls_notify_start_failed(self):
        server = _make_server()
        failures: list[str] = []
        server._start_failed_handler = failures.append

        with patch.object(server, "_create_app", side_effect=RuntimeError("boom")):
            server._current_port = 0
            server._current_host = "127.0.0.1"
            server._startup_notified = False
            server._stop_event.clear()
            server._run_uvicorn()

        self.assertEqual(len(failures), 1)
        self.assertIn("boom", failures[0])

    def test_unexpected_exit_logs_warning(self):
        server = _make_server()

        async def serve_noop(self_server):
            return

        with (
            patch.object(server, "_create_app", return_value=MagicMock()),
            patch("uvicorn.Server.serve", serve_noop),
        ):
            server._current_port = 0
            server._current_host = "127.0.0.1"
            server._startup_notified = True
            server._stop_event.clear()
            with self.assertLogs("pypost.core.metrics_server", level="WARNING") as cm:
                server._run_uvicorn()

        self.assertTrue(any("unexpected_exit" in m for m in cm.output))

    def test_run_uvicorn_drains_pending_task_without_destroyed_warning(self):
        """Regression test for PYPOST-726.

        Mirrors an sse_starlette-style watcher task still pending on the loop
        when uvicorn's serve() returns. Without draining, asyncio would log
        "Task was destroyed but it is pending!" once the orphaned Task is
        garbage-collected after loop.close().
        """
        server = _make_server()
        leftover_tasks: list[asyncio.Task] = []

        async def serve_leaves_pending_task(self_server):
            task = asyncio.get_event_loop().create_task(asyncio.sleep(100))
            leftover_tasks.append(task)
            await asyncio.sleep(0)

        with (
            patch.object(server, "_create_app", return_value=MagicMock()),
            patch("uvicorn.Server.serve", serve_leaves_pending_task),
        ):
            server._current_port = 0
            server._current_host = "127.0.0.1"
            server._startup_notified = True
            server._stop_event.set()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                server._run_uvicorn()
                leftover_tasks.clear()
                import gc

                gc.collect()

        messages = [str(w.message) for w in caught]
        self.assertFalse(
            any("was destroyed but it is pending" in m for m in messages),
            f"unexpected destroyed-task warning(s): {messages}",
        )


class TestMetricsServerRestartServer(unittest.TestCase):
    def test_restart_calls_stop_then_start(self):
        server = _make_server()
        calls: list[str] = []
        with (
            patch.object(server, "stop_server", side_effect=lambda: calls.append("stop")),
            patch.object(server, "start_server", side_effect=lambda h, p: calls.append("start")),
        ):
            server.restart_server("127.0.0.1", 9999)

        self.assertEqual(calls, ["stop", "start"])


if __name__ == "__main__":
    unittest.main()
