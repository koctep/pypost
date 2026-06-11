"""Unit tests for shared uvicorn bind error formatting (PYPOST-154)."""
import errno
import unittest

import pytest

from pypost.core.mcp_server import format_mcp_bind_error
from pypost.core.server_bind import format_bind_error

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


if __name__ == "__main__":
    unittest.main()
