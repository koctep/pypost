"""Lifecycle tests for AsgiServerHost, shared by the metrics and MCP servers."""
import threading
import time
import unittest
from unittest.mock import patch

from pypost.core.asgi_server_host import AsgiServerHost


async def _app(scope, receive, send):  # pragma: no cover - never served
    return None


def _fake_serve():
    """Stand in for _serve: alive until stop() asks the server to exit."""
    def serve(self):
        while not self._server.should_exit:
            time.sleep(0.01)
    return patch.object(AsgiServerHost, "_serve", serve)


class AsgiServerHostTests(unittest.TestCase):
    def _host(self):
        return AsgiServerHost("test", lambda: _app)

    def _release_on_cleanup(self, host):
        """Stop the fake server without taking the host lock.

        Cleaning up through stop() would block on the lock a deadlock leaves
        held, turning a failed assertion into a hung suite.
        """
        def release():
            if host.server is not None:
                host.server.should_exit = True
        self.addCleanup(release)

    def test_server_exists_the_moment_start_returns(self):
        host = self._host()
        with _fake_serve():
            host.start("127.0.0.1", 9099)
            self._release_on_cleanup(host)

            self.assertIsNotNone(host.server)
            self.assertTrue(host.is_running())
            self.assertEqual(("127.0.0.1", 9099), (host.host, host.port))

    def test_stop_right_after_start_asks_the_server_to_exit(self):
        host = self._host()
        with _fake_serve():
            host.start("127.0.0.1", 9099)
            server = host.server
            self._release_on_cleanup(host)

            host.stop()

            self.assertTrue(server.should_exit)
            self.assertIsNone(host.server)
            self.assertIsNone(host.thread)
            self.assertFalse(host.is_running())

    def test_start_on_a_live_host_does_not_deadlock(self):
        """start() calls stop() while holding the lock, so it must be reentrant."""
        host = self._host()
        with _fake_serve():
            host.start("127.0.0.1", 9099)
            self._release_on_cleanup(host)

            done = threading.Event()

            def restart():
                host.start("127.0.0.1", 9100)
                done.set()

            worker = threading.Thread(target=restart, daemon=True)
            worker.start()

            self.assertTrue(
                done.wait(5), "start() deadlocked against its own stop()"
            )
            self.assertEqual(9100, host.port)

    def test_restart_rebinds_the_new_port(self):
        host = self._host()
        with _fake_serve():
            host.start("127.0.0.1", 9099)
            self._release_on_cleanup(host)

            host.restart("127.0.0.1", 9101)

            self.assertEqual(9101, host.port)
            self.assertTrue(host.is_running())

    def test_stop_on_a_host_that_never_started_is_a_noop(self):
        host = self._host()
        host.stop()
        self.assertFalse(host.is_running())


if __name__ == "__main__":
    unittest.main()
