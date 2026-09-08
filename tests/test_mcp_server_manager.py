"""Lifecycle tests for MCPServerManager (thread and uvicorn ownership)."""
import time
import unittest
from unittest.mock import patch

from pypost.core.mcp_server import MCPServerManager


class MCPServerManagerLifecycleTests(unittest.TestCase):
    @staticmethod
    def _fake_uvicorn(manager):
        """Stand in for _run_uvicorn: alive until stop_server asks it to exit."""
        def run(self):
            while not self._server_instance.should_exit:
                time.sleep(0.01)
        return patch.object(type(manager), "_run_uvicorn", run)

    def _release_on_cleanup(self, manager):
        def release():
            if manager._server_instance is not None:
                manager._server_instance.should_exit = True
        self.addCleanup(release)

    def test_server_is_reachable_the_moment_start_returns(self):
        """Built in the caller, not in the thread.

        Assigning it inside _run_uvicorn lets a stop that arrives first read
        None, skip should_exit, and leave the server serving.
        """
        manager = MCPServerManager()
        with self._fake_uvicorn(manager):
            manager.start_server(1099, [])
            self._release_on_cleanup(manager)

            self.assertIsNotNone(manager._server_instance)
            self.assertTrue(manager.is_running())

    def test_stop_right_after_start_asks_the_server_to_exit(self):
        manager = MCPServerManager()
        with self._fake_uvicorn(manager):
            manager.start_server(1099, [])
            server = manager._server_instance
            self._release_on_cleanup(manager)

            manager.stop_server()

            self.assertTrue(server.should_exit)
            self.assertIsNone(manager._server_instance)
            self.assertFalse(manager.is_running())


if __name__ == "__main__":
    unittest.main()
