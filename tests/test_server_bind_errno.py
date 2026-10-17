"""Unit tests for structured errno classification, Windows WSA normalization,
and multi-family (IPv4/IPv6) OS port preflight error handling (PYPOST-1436).
"""
import errno
import socket
import unittest

import pytest

from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.server_bind import (
    BindErrorClassification,
    classify_bind_error,
    detect_address_family,
    extract_errno,
    format_bind_error,
    validate_host_and_port,
)

pytestmark = pytest.mark.timeout(30)


class TestExtractErrno(unittest.TestCase):
    """Test extracting numeric OS error codes across various exception structures."""

    def test_extract_from_standard_errno_attribute(self):
        exc = OSError(errno.EADDRINUSE, "Address already in use")
        self.assertEqual(extract_errno(exc), errno.EADDRINUSE)

    def test_extract_from_winerror_attribute(self):
        exc = OSError("WSA error")
        setattr(exc, "winerror", 10048)
        self.assertEqual(extract_errno(exc), 10048)

    def test_extract_from_args_tuple_int(self):
        exc = OSError(errno.EACCES, "Permission denied")
        exc.errno = None
        self.assertEqual(extract_errno(exc), errno.EACCES)

    def test_extract_from_nested_socket_args(self):
        exc = socket.error((10013, "WSAEACCES"))
        exc.errno = None
        self.assertEqual(extract_errno(exc), 10013)

    def test_returns_none_when_no_numeric_code(self):
        exc = OSError("Arbitrary unclassified error without code")
        exc.errno = None
        self.assertIsNone(extract_errno(exc))


class TestClassifyBindError(unittest.TestCase):
    """Test structured classification of POSIX, BSD, and Windows networking errors."""

    def test_posix_port_in_use(self):
        exc = OSError(errno.EADDRINUSE, "Address already in use")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.PORT_IN_USE)

    def test_bsd_macos_port_in_use(self):
        exc = OSError(48, "Address already in use")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.PORT_IN_USE)

    def test_windows_wsa_port_in_use_10048(self):
        exc = OSError(10048, "WSAEADDRINUSE")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.PORT_IN_USE)

    def test_posix_address_not_available(self):
        exc = OSError(errno.EADDRNOTAVAIL, "Cannot assign requested address")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.ADDRESS_NOT_AVAILABLE)

    def test_bsd_macos_address_not_available(self):
        exc = OSError(49, "Cannot assign requested address")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.ADDRESS_NOT_AVAILABLE)

    def test_windows_wsa_address_not_available_10049(self):
        exc = OSError(10049, "WSAEADDRNOTAVAIL")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.ADDRESS_NOT_AVAILABLE)

    def test_posix_permission_denied_eacces(self):
        exc = OSError(errno.EACCES, "Permission denied")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.PERMISSION_DENIED)

    def test_posix_permission_denied_eperm(self):
        exc = OSError(errno.EPERM, "Operation not permitted")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.PERMISSION_DENIED)

    def test_windows_wsa_permission_denied_10013(self):
        exc = OSError(10013, "WSAEACCES")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.PERMISSION_DENIED)

    def test_unclassified_error(self):
        exc = OSError(errno.ENOENT, "No such file or directory")
        self.assertEqual(classify_bind_error(exc), BindErrorClassification.UNCLASSIFIED)


class TestLocalizedBindErrorFormatting(unittest.TestCase):
    """Test that format_bind_error correctly classifies errors regardless of
    system locale/language.
    """

    def test_german_strerror_eaddrinuse(self):
        # German locale: "Die Adresse wird bereits verwendet"
        exc = OSError(errno.EADDRINUSE, "Die Adresse wird bereits verwendet")
        msg = format_bind_error(exc, "127.0.0.1", 8080, "server")
        self.assertIn("8080", msg)
        self.assertIn("port is busy or unavailable", msg)
        self.assertIn("Settings", msg)

    def test_french_strerror_eaddrinuse(self):
        # French locale: "Adresse déjà utilisée"
        exc = OSError(errno.EADDRINUSE, "Adresse déjà utilisée")
        msg = format_bind_error(exc, "0.0.0.0", 9000, "metrics")
        self.assertIn("9000", msg)
        self.assertIn("port is busy or unavailable", msg)

    def test_japanese_strerror_eaddrinuse(self):
        # Japanese locale: "アドレスは既に使用されています"
        exc = OSError(errno.EADDRINUSE, "アドレスは既に使用されています")
        msg = format_bind_error(exc, "localhost", 7000, "mcp")
        self.assertIn("7000", msg)
        self.assertIn("port is busy or unavailable", msg)

    def test_dual_argument_order_support(self):
        # Support format_bind_error("127.0.0.1", 8080, exc) and
        # format_bind_error(exc, "127.0.0.1", 8080)
        exc = OSError(errno.EADDRINUSE, "Die Adresse wird bereits verwendet")
        msg1 = format_bind_error("127.0.0.1", 8080, exc)
        msg2 = format_bind_error(exc, "127.0.0.1", 8080, "server")
        self.assertIn("8080", msg1)
        self.assertIn("port is busy or unavailable", msg1)
        self.assertIn("8080", msg2)
        self.assertIn("port is busy or unavailable", msg2)

    def test_permission_denied_formatting(self):
        exc = OSError(errno.EACCES, "Permission denied")
        msg = format_bind_error(exc, "127.0.0.1", 80, "server")
        self.assertIn("permission denied", msg.lower())
        self.assertNotIn("busy", msg.lower())

    def test_address_not_available_formatting(self):
        exc = OSError(errno.EADDRNOTAVAIL, "Cannot assign requested address")
        msg = format_bind_error(exc, "192.0.2.1", 8080, "server")
        self.assertIn("address not available", msg.lower())
        self.assertNotIn("busy", msg.lower())


class TestDetectAddressFamily(unittest.TestCase):
    """Test address family detection for IPv4 and IPv6 strings."""

    def test_detect_ipv4_standard(self):
        self.assertEqual(detect_address_family("127.0.0.1"), socket.AF_INET)
        self.assertEqual(detect_address_family("0.0.0.0"), socket.AF_INET)
        self.assertEqual(detect_address_family("192.168.1.1"), socket.AF_INET)

    def test_detect_ipv6_standard(self):
        self.assertEqual(detect_address_family("::1"), socket.AF_INET6)
        self.assertEqual(detect_address_family("::"), socket.AF_INET6)
        self.assertEqual(detect_address_family("2001:db8::1"), socket.AF_INET6)

    def test_detect_ipv6_bracketed(self):
        self.assertEqual(detect_address_family("[::1]"), socket.AF_INET6)
        self.assertEqual(detect_address_family("[::]"), socket.AF_INET6)

    def test_detect_hostnames(self):
        self.assertEqual(detect_address_family("localhost"), socket.AF_INET)
        self.assertEqual(detect_address_family("example.internal"), socket.AF_INET)


class TestValidateHostAndPort(unittest.TestCase):
    """Test preflight validation probing on IPv4 and IPv6."""

    def test_validate_free_ipv4_port(self):
        # Binding to a dynamic free port should succeed without error
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]
        validate_host_and_port("127.0.0.1", free_port)

    def test_validate_occupied_ipv4_port_raises_value_error(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            port = s.getsockname()[1]

            with self.assertRaises(ValueError) as ctx:
                validate_host_and_port("127.0.0.1", port)
            self.assertIn(str(port), str(ctx.exception))
            self.assertIn("unavailable", str(ctx.exception).lower())

    def test_validate_free_ipv6_port(self):
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                s.bind(("::1", 0))
                free_port = s.getsockname()[1]
        except OSError:
            self.skipTest("IPv6 ::1 loopback not available on this environment")

        validate_host_and_port("::1", free_port)
        validate_host_and_port("[::1]", free_port)

    def test_validate_occupied_ipv6_port_raises_value_error(self):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("::1", 0))
            s.listen(1)
            port = s.getsockname()[1]
        except OSError:
            self.skipTest("IPv6 ::1 loopback not available on this environment")

        try:
            with self.assertRaises(ValueError) as ctx:
                validate_host_and_port("::1", port)
            self.assertIn(str(port), str(ctx.exception))
            self.assertIn("unavailable", str(ctx.exception).lower())
        finally:
            s.close()

    def test_mcp_server_registry_validate_os_port_supports_ipv6(self):
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                s.bind(("::1", 0))
                free_port = s.getsockname()[1]
        except OSError:
            self.skipTest("IPv6 ::1 loopback not available on this environment")

        # In unpatched code, MCPServerRegistry._validate_os_port hardcodes AF_INET,
        # which fails on ::1 even if the port is free!
        MCPServerRegistry._validate_os_port("::1", free_port)


class TestObservabilityLogging(unittest.TestCase):
    """Test structured event logging and syslog level mapping for bind observability."""

    def test_detect_address_family_logs_debug(self):
        with self.assertLogs("pypost.core.server_bind", level="DEBUG") as cm:
            family = detect_address_family("127.0.0.1")
        self.assertEqual(family, socket.AF_INET)
        self.assertTrue(
            any("detect_address_family host=127.0.0.1 family=AF_INET" in msg for msg in cm.output)
        )

    def test_validate_host_and_port_logs_info_on_success(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]
        with self.assertLogs("pypost.core.server_bind", level="INFO") as cm:
            validate_host_and_port("127.0.0.1", free_port)
        self.assertTrue(
            any("validate_host_and_port_succeeded" in msg for msg in cm.output)
        )

    def test_validate_host_and_port_logs_warning_on_occupied_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            port = s.getsockname()[1]

            with self.assertLogs("pypost.core.server_bind", level="WARNING") as cm:
                with self.assertRaises(ValueError):
                    validate_host_and_port("127.0.0.1", port)
            self.assertTrue(
                any("validate_host_and_port_failed" in msg and "port_in_use" in msg
                    for msg in cm.output)
            )

    def test_mcp_server_registry_validate_os_port_logs_warning(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            port = s.getsockname()[1]

            with self.assertLogs("pypost.core.mcp_server_registry", level="WARNING") as cm:
                with self.assertRaises(ValueError):
                    MCPServerRegistry._validate_os_port("127.0.0.1", port)
            self.assertTrue(
                any("mcp_server_registry_port_validation_failed" in msg for msg in cm.output)
            )


if __name__ == "__main__":
    unittest.main()
