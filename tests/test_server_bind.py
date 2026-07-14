"""Unit tests for shared uvicorn lifecycle helpers: bind error formatting
(PYPOST-154) and pending-task draining before loop close (PYPOST-726)."""
import asyncio
import errno
import unittest

import pytest

from pypost.core.qt.mcp_server import format_mcp_bind_error
from pypost.core.server_bind import drain_pending_tasks, format_bind_error

pytestmark = pytest.mark.timeout(30)


class TestFormatBindError(unittest.TestCase):
    def test_addr_in_use_message_includes_port_and_guidance(self):
        exc = OSError("Address already in use")
        exc.errno = errno.EADDRINUSE
        message = format_bind_error(exc, "127.0.0.1", 9080, "metrics server")
        self.assertIn("9080", message)
        self.assertIn("busy", message.lower())
        self.assertIn("Settings", message)

    def test_mcp_wrapper_uses_shared_message(self):
        exc = OSError("Address already in use")
        exc.errno = errno.EADDRINUSE
        message = format_mcp_bind_error(exc, "127.0.0.1", 1080)
        self.assertIn("MCP server", message)
        self.assertIn("1080", message)
        self.assertIn("busy", message.lower())

    def test_generic_oserror_uses_strerror(self):
        exc = OSError("Permission denied")
        exc.errno = errno.EACCES
        message = format_bind_error(exc, "0.0.0.0", 8080, "test server")
        self.assertIn("Permission denied", message)
        self.assertNotIn("busy", message.lower())


class TestDrainPendingTasks(unittest.TestCase):
    def test_cancels_and_awaits_pending_task(self):
        loop = asyncio.new_event_loop()
        try:
            task = loop.create_task(asyncio.sleep(100))
            # Let the task get scheduled onto the loop before draining it.
            loop.run_until_complete(asyncio.sleep(0))
            self.assertIn(task, asyncio.all_tasks(loop))

            drain_pending_tasks(loop)

            self.assertTrue(task.done())
            self.assertTrue(task.cancelled())
            self.assertEqual(asyncio.all_tasks(loop), set())
            # Closing a fully-drained loop must not raise or warn.
            loop.close()
        finally:
            if not loop.is_closed():
                loop.close()

    def test_noop_when_no_pending_tasks(self):
        loop = asyncio.new_event_loop()
        try:
            self.assertEqual(asyncio.all_tasks(loop), set())
            drain_pending_tasks(loop)  # should not raise
            loop.close()
        finally:
            if not loop.is_closed():
                loop.close()

    def test_lets_task_run_cleanup_on_cancellation(self):
        loop = asyncio.new_event_loop()
        cleanup_ran = []

        async def watcher():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                cleanup_ran.append(True)
                raise

        try:
            loop.create_task(watcher())
            loop.run_until_complete(asyncio.sleep(0))

            drain_pending_tasks(loop)

            self.assertEqual(cleanup_ran, [True])
            loop.close()
        finally:
            if not loop.is_closed():
                loop.close()


if __name__ == "__main__":
    unittest.main()
