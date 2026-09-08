"""MCPServerManager delegates its server lifecycle to AsgiServerHost."""
import unittest
from unittest.mock import MagicMock

from pypost.core.mcp_server import MCPServerManager
from pypost.models.models import RequestData


class MCPServerManagerLifecycleTests(unittest.TestCase):
    def _manager(self):
        manager = MCPServerManager()
        manager._server_host = MagicMock()
        return manager

    def test_start_registers_tools_and_starts_the_host(self):
        manager = self._manager()
        tool = RequestData(method="GET", url="http://x", name="T", expose_as_mcp=True)

        manager.start_server(1099, [tool], host="127.0.0.1")

        manager._server_host.start.assert_called_once_with("127.0.0.1", 1099)
        self.assertEqual([tool], list(manager._impl.tools_map.values()))

    def test_start_emits_running_status(self):
        manager = self._manager()
        seen = []
        manager.status_changed.connect(seen.append)

        manager.start_server(1099, [])

        self.assertEqual([True], seen)

    def test_stop_on_a_running_server_stops_the_host_and_emits(self):
        manager = self._manager()
        manager._server_host.is_running.return_value = True
        seen = []
        manager.status_changed.connect(seen.append)

        manager.stop_server()

        manager._server_host.stop.assert_called_once_with()
        self.assertEqual([False], seen)

    def test_stop_on_a_stopped_server_does_nothing(self):
        manager = self._manager()
        manager._server_host.is_running.return_value = False
        seen = []
        manager.status_changed.connect(seen.append)

        manager.stop_server()

        manager._server_host.stop.assert_not_called()
        self.assertEqual([], seen)


if __name__ == "__main__":
    unittest.main()
