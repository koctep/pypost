"""Pure unit tests for MetricsServer lifecycle (PYPOST-720, PYPOST-726)."""
import asyncio
import threading
import unittest
import warnings
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import (
    MetricsServer,
    _ServerGeneration,
    _install_thread_exit,
    _uninstall_thread_exit,
)

pytestmark = pytest.mark.timeout(30)


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


class TestMetricsServerGenerations(unittest.TestCase):
    def test_stop_waits_for_already_claimed_generation_callback(self):
        server = _make_server()
        callback_entered = threading.Event()
        release_callback = threading.Event()
        stop_entered = threading.Event()
        stop_done = threading.Event()

        def listening_changed(_value):
            callback_entered.set()
            self.assertTrue(release_callback.wait(timeout=1.0))

        generation = _ServerGeneration(
            1,
            "127.0.0.1",
            9001,
            threading.Event(),
            listening_changed=listening_changed,
        )
        server._active_generation = generation

        callback_thread = threading.Thread(
            target=server._notify_started, args=(generation,)
        )
        callback_thread.start()
        self.assertTrue(callback_entered.wait(timeout=1.0))

        def stop():
            stop_entered.set()
            server.stop_server()
            stop_done.set()

        stop_thread = threading.Thread(target=stop)
        stop_thread.start()
        self.assertTrue(stop_entered.wait(timeout=1.0))
        self.assertFalse(stop_done.wait(timeout=0.05))
        release_callback.set()
        callback_thread.join(timeout=1.0)
        stop_thread.join(timeout=1.0)

        self.assertTrue(stop_done.is_set())
        self.assertIsNone(server._active_generation)

    def test_restart_cannot_overtake_claimed_start_failure_callback(self):
        server = _make_server()
        callback_entered = threading.Event()
        release_callback = threading.Event()
        restart_done = threading.Event()

        def start_failed(_message):
            callback_entered.set()
            self.assertTrue(release_callback.wait(timeout=1.0))

        generation = _ServerGeneration(
            1,
            "127.0.0.1",
            9001,
            threading.Event(),
            start_failed_handler=start_failed,
        )
        server._active_generation = generation
        callback_thread = threading.Thread(
            target=server._notify_start_failed,
            args=("safe failure", generation),
        )
        callback_thread.start()
        self.assertTrue(callback_entered.wait(timeout=1.0))

        with patch.object(server, "start_server") as start_server:
            def restart():
                server.stop_server()
                start_server("127.0.0.1", 9002)
                restart_done.set()

            restart_thread = threading.Thread(target=restart)
            restart_thread.start()
            self.assertFalse(restart_done.wait(timeout=0.05))
            release_callback.set()
            callback_thread.join(timeout=1.0)
            restart_thread.join(timeout=1.0)

        self.assertTrue(restart_done.is_set())
        start_server.assert_called_once_with("127.0.0.1", 9002)

    def test_normal_stop_wins_interleaving_with_worker_finalization(self):
        server = _make_server()
        unexpected: list[str] = []
        generation = _ServerGeneration(
            1,
            "127.0.0.1",
            9001,
            threading.Event(),
            startup_notified=True,
            unexpected_exit=unexpected.append,
        )
        server._active_generation = generation
        server._is_listening = True

        with generation.callback_lock:
            finalizer = threading.Thread(
                target=server._finalize_generation, args=(generation,)
            )
            finalizer.start()
            server.stop_server()
        finalizer.join(timeout=1.0)

        self.assertFalse(finalizer.is_alive())
        self.assertEqual(unexpected, [])
        self.assertFalse(server.is_listening)

    def test_process_exit_dispatch_is_isolated_for_overlapping_workers(self):
        original_exit = __import__("sys").exit
        installed = threading.Barrier(3)
        release = threading.Event()
        failures: list[str] = []

        def worker(label):
            def thread_exit(_code):
                raise RuntimeError(label)

            _install_thread_exit(thread_exit)
            try:
                installed.wait(timeout=1.0)
                try:
                    __import__("sys").exit(1)
                except RuntimeError as exc:
                    failures.append(str(exc))
                self.assertTrue(release.wait(timeout=1.0))
            finally:
                _uninstall_thread_exit()

        workers = [
            threading.Thread(target=worker, args=(label,))
            for label in ("first", "second")
        ]
        for worker_thread in workers:
            worker_thread.start()
        installed.wait(timeout=1.0)
        self.assertIsNot(__import__("sys").exit, original_exit)
        release.set()
        for worker_thread in workers:
            worker_thread.join(timeout=1.0)

        self.assertEqual(sorted(failures), ["first", "second"])
        self.assertIs(__import__("sys").exit, original_exit)

    def test_stale_worker_finalization_cannot_mutate_active_restart(self):
        server = _make_server()
        unexpected: list[str] = []
        old = _ServerGeneration(
            1,
            "127.0.0.1",
            9001,
            threading.Event(),
            startup_notified=True,
            unexpected_exit=unexpected.append,
        )
        current = _ServerGeneration(2, "127.0.0.1", 9002, threading.Event())
        current_instance = object()
        server._active_generation = current
        server.server_instance = current_instance
        server._is_listening = True

        async def serve_noop(_uvicorn_server):
            return None

        with (
            patch.object(server, "_create_app", return_value=MagicMock()),
            patch("uvicorn.Server.serve", serve_noop),
        ):
            server._run_uvicorn(old)

        self.assertTrue(server.is_listening)
        self.assertIs(server.server_instance, current_instance)
        self.assertEqual(unexpected, [])

    def test_stale_generation_start_failure_is_not_delivered(self):
        server = _make_server()
        failures: list[str] = []
        old = _ServerGeneration(
            1,
            "127.0.0.1",
            9001,
            threading.Event(),
            start_failed_handler=failures.append,
        )
        server._active_generation = _ServerGeneration(
            2, "127.0.0.1", 9002, threading.Event()
        )

        server._notify_start_failed("stale bind failure", old)

        self.assertEqual(failures, [])
        self.assertIsNone(server._pending_start_failure)

    def test_stop_does_not_hold_lifecycle_lock_while_joining(self):
        server = _make_server()
        lock_acquired = threading.Event()

        def probe_join(timeout):
            def acquire_lock():
                with server.server_lock:
                    lock_acquired.set()

            contender = threading.Thread(target=acquire_lock)
            contender.start()
            contender.join(timeout=0.5)

        thread = MagicMock(spec=threading.Thread)
        thread.join.side_effect = probe_join
        generation = _ServerGeneration(
            1, "127.0.0.1", 9001, threading.Event(), thread=thread
        )
        server._active_generation = generation
        server.thread = thread

        server.stop_server()

        self.assertTrue(lock_acquired.is_set())


class TestMetricsServerBindWarning(unittest.TestCase):
    @patch.object(MetricsServer, "stop_server")
    @patch("pypost.core.metrics_server.threading.Thread")
    def test_start_server_warns_on_non_localhost_bind(self, mock_thread, mock_stop):
        server = _make_server()
        with self.assertLogs("pypost.core.metrics_server", level="WARNING") as logs:
            server.start_server("0.0.0.0", 9080)
        self.assertTrue(
            any("metrics_server_non_localhost_bind" in record.message for record in logs.records)
        )

    @patch.object(MetricsServer, "stop_server")
    @patch("pypost.core.metrics_server.threading.Thread")
    def test_start_server_no_warning_for_loopback(self, mock_thread, mock_stop):
        server = _make_server()
        with self.assertLogs("pypost.core.metrics_server", level="INFO") as logs:
            server.start_server("127.0.0.1", 9080)
        self.assertFalse(
            any("metrics_server_non_localhost_bind" in record.message for record in logs.records)
        )


if __name__ == "__main__":
    unittest.main()
