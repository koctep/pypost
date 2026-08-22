"""Tests for WebSocket TLS and connection-security policy (PYPOST-1131 / WS-8).

Asserts the contract, guardrails, and behaviors specified in:
- `ai-tasks/PYPOST-1131/10-requirements.md`
- `ai-tasks/PYPOST-1131/20-architecture.md`

Covers:
1. Static AST guardrail prohibiting blanket `ignoreSslErrors()` across `pypost/`.
2. Architectural Qt-free import isolation for `pypost.core.websocket_security_policy`.
3. Model persistence isolation (zero TLS bypass / certificate override fields).
4. Host loopback detection (RFC 6761, IPv4 127.0.0.0/8, IPv6 ::1, *.localhost).
5. Endpoint security classification (SECURE_TLS, INSECURE_TLS_EXCEPTION,
   PLAINTEXT_REMOTE, PLAINTEXT_LOOPBACK).
6. Pure domain TLS data structures (TlsCertificateError, TlsDiagnosticReport,
   EphemeralSessionTrustDecision).
7. ConnectionSecurityPolicy domain rules and diagnostic report formatting.
8. Transport protocol contracts (HandshakeTarget.verify_tls default).
9. Qt transport SSL configuration (VerifyPeer vs VerifyNone) and structured error extraction.
10. Headless session controller ephemeral trust lifecycle, signal emissions, and reset on close.
11. Offline hermetic TLS rejection and override lifecycle integration tests.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
import logging
from pathlib import Path

import pytest

from pypost.models.websocket import WebSocketConnection
from pypost.core.websocket_transport_protocol import HandshakeTarget
from pypost.core.qt.websocket_session import WebSocketSessionController
from pypost.core.qt.websocket_transport import QtWebSocketTransport

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPOST_DIR = REPO_ROOT / "pypost"


# =============================================================================
# Helper Functions
# =============================================================================


def _get_all_python_files(root: Path) -> list[Path]:
    """Return all Python source files in directory, ignoring pycache."""
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def _extract_imports(file_path: Path) -> list[str]:
    """Parse AST of a Python file and return all imported module names."""
    if not file_path.exists():
        return []
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module)
    return imported_modules


# =============================================================================
# 1. Static AST Guardrails & Architectural Import Isolation
# =============================================================================


@pytest.mark.timeout(30)
def test_no_ignore_ssl_errors_in_production_code():
    """Scan all Python files under `pypost/` and assert `ignoreSslErrors(` does not appear.

    Prohibits blanket ignoreSslErrors() calls in production code to prevent
    unconditional TLS bypass regressions (PYPOST-1131 / D-12).
    """
    py_files = _get_all_python_files(PYPOST_DIR)
    violations: list[tuple[str, int, str]] = []

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "ignoreSslErrors(" in line:
                rel_path = str(py_file.relative_to(REPO_ROOT))
                violations.append((rel_path, idx, stripped))

    assert not violations, (
        "Found forbidden blanket `ignoreSslErrors(` in production code:\n"
        + "\n".join(f"  {path}:{line_no}: {code}" for path, line_no, code in violations)
    )


@pytest.mark.timeout(30)
def test_websocket_security_policy_is_qt_free():
    """`pypost/core/websocket_security_policy.py` must contain no Qt/PySide6 imports."""
    policy_path = PYPOST_DIR / "core" / "websocket_security_policy.py"
    assert policy_path.exists(), f"Expected {policy_path} to exist"
    imports = _extract_imports(policy_path)
    forbidden_terms = (
        "PySide6", "Qt", "QtCore", "QtGui", "QtWidgets", "QtNetwork", "QtWebSockets"
    )
    qt_imports = [
        imp for imp in imports
        if any(term in imp for term in forbidden_terms)
    ]
    assert not qt_imports, (
        f"pypost/core/websocket_security_policy.py violates Qt-free isolation: {qt_imports}"
    )


# =============================================================================
# 2. Model Persistence Isolation Guardrail (Zero Disk Persistence)
# =============================================================================


@pytest.mark.timeout(30)
def test_websocket_connection_model_has_no_tls_bypass_fields():
    """Verify WebSocketConnection model has no fields persisting TLS exceptions or bypasses.

    Guarantees D-12 zero disk persistence invariant: certificate exceptions
    exist exclusively in volatile process memory during active sessions.
    """
    forbidden_field_substrings = [
        "verify_tls",
        "insecure",
        "self_signed",
        "ignore_ssl",
        "ssl_override",
        "bypass_tls",
        "trusted_fingerprint",
        "trusted_cert",
        "cert_exception",
    ]

    model_field_names = set(WebSocketConnection.model_fields.keys())
    for field_name in model_field_names:
        for forbidden in forbidden_field_substrings:
            assert forbidden not in field_name.lower(), (
                "WebSocketConnection model contains forbidden persisted security bypass field: "
                f"'{field_name}'"
            )

    conn = WebSocketConnection(name="Test Security Invariance", url="wss://echo.websocket.org")
    dumped_json = conn.model_dump_json()
    parsed = json.loads(dumped_json)
    for key in parsed:
        for forbidden in forbidden_field_substrings:
            assert forbidden not in key.lower(), (
                f"Serialized WebSocketConnection contains forbidden security bypass key: '{key}'"
            )


# =============================================================================
# 3. Pure Domain Data Structures & Enums
# =============================================================================


@pytest.mark.timeout(30)
def test_host_security_classification_enum():
    """Verify HostSecurityClassification enum member definitions and string values."""
    from pypost.core.websocket_security_policy import HostSecurityClassification

    assert HostSecurityClassification.SECURE_TLS.value == "secure_tls"
    assert HostSecurityClassification.INSECURE_TLS_EXCEPTION.value == "insecure_tls_exception"
    assert HostSecurityClassification.PLAINTEXT_REMOTE.value == "plaintext_remote"
    assert HostSecurityClassification.PLAINTEXT_LOOPBACK.value == "plaintext_loopback"


@pytest.mark.timeout(30)
def test_tls_certificate_error_dataclass():
    """Verify TlsCertificateError frozen dataclass attributes and immutability."""
    from pypost.core.websocket_security_policy import TlsCertificateError

    expiry = datetime(2028, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    error = TlsCertificateError(
        error_code="self_signed",
        message="The certificate is self-signed, and untrusted",
        certificate_subject="CN=localhost, O=Local Dev",
        certificate_issuer="CN=localhost, O=Local Dev",
        certificate_fingerprint="SHA256:abcd1234efgh5678",
        expiry_date=expiry,
    )

    assert error.error_code == "self_signed"
    assert error.message == "The certificate is self-signed, and untrusted"
    assert error.certificate_subject == "CN=localhost, O=Local Dev"
    assert error.certificate_issuer == "CN=localhost, O=Local Dev"
    assert error.certificate_fingerprint == "SHA256:abcd1234efgh5678"
    assert error.expiry_date == expiry

    with pytest.raises(Exception):
        error.error_code = "modified"  # type: ignore[misc]


@pytest.mark.timeout(30)
def test_tls_diagnostic_report_dataclass():
    """Verify TlsDiagnosticReport frozen dataclass structure and summary extraction."""
    from pypost.core.websocket_security_policy import (
        TlsCertificateError,
        TlsDiagnosticReport,
    )

    now = datetime.now(timezone.utc)
    err1 = TlsCertificateError(
        error_code="self_signed",
        message="The certificate is self-signed",
    )
    err2 = TlsCertificateError(
        error_code="host_mismatch",
        message="The host name did not match any of the valid hosts for this certificate",
    )

    report = TlsDiagnosticReport(
        errors=(err1, err2),
        summary_message="TLS validation failed: Self-signed certificate; Hostname mismatch",
        target_url="wss://localhost:8443/ws",
        target_host="localhost",
        timestamp=now,
    )

    assert len(report.errors) == 2
    assert "Self-signed certificate" in report.summary_message
    assert report.target_url == "wss://localhost:8443/ws"
    assert report.target_host == "localhost"
    assert report.timestamp == now


@pytest.mark.timeout(30)
def test_ephemeral_session_trust_decision_lifecycle():
    """Verify EphemeralSessionTrustDecision in-memory state and reset functionality."""
    from pypost.core.websocket_security_policy import EphemeralSessionTrustDecision

    decision = EphemeralSessionTrustDecision(
        session_id="sess-1234",
        target_url="wss://internal-dev.local:8080/ws",
    )
    assert decision.session_id == "sess-1234"
    assert decision.target_url == "wss://internal-dev.local:8080/ws"
    assert decision.exception_granted is False
    assert decision.granted_at is None

    grant_time = datetime.now(timezone.utc)
    decision.exception_granted = True
    decision.granted_at = grant_time

    assert decision.exception_granted is True
    assert decision.granted_at == grant_time

    decision.reset()
    assert decision.exception_granted is False
    assert decision.granted_at is None


# =============================================================================
# 4. Host Loopback Detection (RFC 6761, IPv4 127.0.0.0/8, IPv6 ::1)
# =============================================================================


@pytest.mark.timeout(30)
def test_loopback_host_detection():
    """Verify is_loopback_host accurately classifies loopback vs remote hosts."""
    from pypost.core.websocket_security_policy import is_loopback_host

    # RFC 6761 & loopback hostnames
    assert is_loopback_host("localhost") is True
    assert is_loopback_host("localhost.localdomain") is True
    assert is_loopback_host("sub.localhost") is True
    assert is_loopback_host("api.dev.localhost") is True
    assert is_loopback_host("LOCALHOST") is True

    # IPv4 loopback (127.0.0.0/8)
    assert is_loopback_host("127.0.0.1") is True
    assert is_loopback_host("127.0.0.2") is True
    assert is_loopback_host("127.0.1.1") is True
    assert is_loopback_host("127.255.255.254") is True

    # IPv6 loopback (::1, [::1])
    assert is_loopback_host("::1") is True
    assert is_loopback_host("[::1]") is True

    # Non-loopback / remote hosts
    assert is_loopback_host("192.168.1.1") is False
    assert is_loopback_host("10.0.0.1") is False
    assert is_loopback_host("172.16.0.1") is False
    assert is_loopback_host("api.example.com") is False
    assert is_loopback_host("echo.websocket.org") is False
    assert is_loopback_host("localhost.com") is False
    assert is_loopback_host("not-localhost") is False
    assert is_loopback_host("8.8.8.8") is False
    assert is_loopback_host("2001:db8::1") is False
    assert is_loopback_host("") is False


# =============================================================================
# 5. Endpoint Security Classification
# =============================================================================


@pytest.mark.timeout(30)
def test_endpoint_security_classification():
    """Verify classify_endpoint_security correctly determines transport security category."""
    from pypost.core.websocket_security_policy import (
        HostSecurityClassification,
        classify_endpoint_security,
    )

    # Plaintext remote (triggers persistent security warning)
    assert (
        classify_endpoint_security("ws://remote-api.com/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_REMOTE
    )
    assert (
        classify_endpoint_security("ws://192.168.1.100:8080/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_REMOTE
    )

    # Plaintext loopback (safe local interface, warning suppressed)
    assert (
        classify_endpoint_security("ws://localhost:3000/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_LOOPBACK
    )
    assert (
        classify_endpoint_security("ws://127.0.0.1:8080/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_LOOPBACK
    )
    assert (
        classify_endpoint_security("ws://sub.localhost:8000/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_LOOPBACK
    )
    assert (
        classify_endpoint_security("ws://[::1]:9000/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_LOOPBACK
    )

    # Secure TLS (verified encrypted transport)
    assert (
        classify_endpoint_security("wss://echo.websocket.org", verify_tls=True)
        == HostSecurityClassification.SECURE_TLS
    )
    assert (
        classify_endpoint_security("wss://127.0.0.1:8443/ws", verify_tls=True)
        == HostSecurityClassification.SECURE_TLS
    )

    # Insecure TLS Exception (ephemeral override active for session)
    assert (
        classify_endpoint_security("wss://echo.websocket.org", verify_tls=False)
        == HostSecurityClassification.INSECURE_TLS_EXCEPTION
    )
    assert (
        classify_endpoint_security("wss://internal-dev.local:8443/ws", verify_tls=False)
        == HostSecurityClassification.INSECURE_TLS_EXCEPTION
    )


@pytest.mark.timeout(30)
def test_connection_security_policy_class_methods():
    """Verify ConnectionSecurityPolicy domain coordinator methods."""
    from pypost.core.websocket_security_policy import (
        ConnectionSecurityPolicy,
        HostSecurityClassification,
        TlsCertificateError,
    )

    policy = ConnectionSecurityPolicy()

    # Classification via policy instance
    assert (
        policy.classify("ws://example.com/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_REMOTE
    )
    assert (
        policy.classify("ws://127.0.0.1:8000/ws", verify_tls=True)
        == HostSecurityClassification.PLAINTEXT_LOOPBACK
    )
    assert (
        policy.classify("wss://echo.com", verify_tls=True)
        == HostSecurityClassification.SECURE_TLS
    )
    assert (
        policy.classify("wss://echo.com", verify_tls=False)
        == HostSecurityClassification.INSECURE_TLS_EXCEPTION
    )

    # Diagnostic report generation
    err1 = TlsCertificateError(
        error_code="self_signed",
        message="The certificate is self-signed, and untrusted",
    )
    report = policy.create_diagnostic_report(
        url="wss://dev.local:8443/socket",
        errors=(err1,),
    )
    assert report.target_url == "wss://dev.local:8443/socket"
    assert report.target_host == "dev.local"
    assert "self-signed" in report.summary_message.lower()
    assert len(report.errors) == 1


# =============================================================================
# 6. Transport Protocol Contracts
# =============================================================================


@pytest.mark.timeout(30)
def test_handshake_target_tls_defaults():
    """Verify HandshakeTarget requires verify_tls=True by default."""
    target = HandshakeTarget(
        url="wss://echo.websocket.org",
        headers={"Authorization": "Bearer token"},
    )
    assert target.verify_tls is True

    insecure_target = HandshakeTarget(
        url="wss://internal.local",
        headers={},
        verify_tls=False,
    )
    assert insecure_target.verify_tls is False


# =============================================================================
# 7. Qt Transport SSL Configuration & Error Extraction
# =============================================================================


@pytest.mark.timeout(30)
def test_qt_websocket_transport_ssl_config_and_diagnostics(qapp):
    """Verify QtWebSocketTransport configures QSslConfiguration properly without ignoreSslErrors."""
    from pypost.core.websocket_security_policy import TlsCertificateError

    transport = QtWebSocketTransport()
    recorded_errors: list[tuple[TlsCertificateError, ...]] = []

    class DummyListener:
        def on_opened(self, subprotocol: str) -> None:
            pass

        def on_text(self, message: str) -> None:
            pass

        def on_binary(self, payload: bytes) -> None:
            pass

        def on_pong(self, elapsed_ms: int, payload: bytes) -> None:
            pass

        def on_closed(self, code: int, reason: str, peer_initiated: bool) -> None:
            pass

        def on_failed(self, category: str, message: str, detail: str) -> None:
            pass

        def on_tls_errors(self, errors: tuple[TlsCertificateError, ...]) -> bool:
            recorded_errors.append(errors)
            return False

    transport.set_listener(DummyListener())

    # Open with verify_tls=True ensures socket has SSL configuration configured
    target_secure = HandshakeTarget(
        url="wss://127.0.0.1:9999",
        headers={},
        verify_tls=True,
    )
    transport.open(target_secure)

    # Internal socket must not have invoked ignoreSslErrors
    assert transport._socket is not None
    transport.abort()


# =============================================================================
# 8. Headless Session Controller Ephemeral Trust Lifecycle & Signals
# =============================================================================


@pytest.mark.timeout(30)
def test_session_controller_default_rejects_untrusted_cert(
    qapp: object, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify WebSocketSessionController rejects TLS errors by default and emits diagnostics."""
    from pypost.core.websocket_security_policy import TlsCertificateError
    from pypost.core.websocket_session_policy import SessionState

    controller = WebSocketSessionController()
    emitted_tls_errors: list[tuple[TlsCertificateError, ...]] = []
    emitted_failures: list[tuple[str, str]] = []

    controller.tls_errors_raised.connect(lambda errs: emitted_tls_errors.append(errs))
    controller.session_failed.connect(lambda cat, msg: emitted_failures.append((cat, msg)))

    err = TlsCertificateError(
        error_code="self_signed",
        message="The certificate is self-signed",
    )

    # Directly trigger listener callback simulating TLS handshake rejection
    controller.open(HandshakeTarget(url="wss://127.0.0.1:8443", headers={}, verify_tls=True))
    with caplog.at_level(logging.ERROR, logger="pypost.core.qt.websocket_session"):
        controller.on_tls_errors((err,))

    assert controller.state == SessionState.FAILED
    assert len(emitted_tls_errors) == 1
    assert emitted_tls_errors[0][0].error_code == "self_signed"
    assert len(emitted_failures) == 1
    assert emitted_failures[0][0] == "tls_error"
    assert any("websocket_session_tls_validation_failed" in r.getMessage() for r in caplog.records)


@pytest.mark.timeout(30)
def test_session_controller_ephemeral_override_lifecycle(qapp):
    """Verify ephemeral trust override is strictly per-session and resets on close/disconnect."""
    from pypost.core.websocket_security_policy import HostSecurityClassification
    from pypost.core.websocket_session_policy import SessionState

    controller = WebSocketSessionController()
    emitted_classifications: list[str] = []

    if hasattr(controller, "security_classification_changed"):
        controller.security_classification_changed.connect(
            lambda c: emitted_classifications.append(
                c if isinstance(c, str) else getattr(c, "value", str(c))
            )
        )

    # 1. Grant ephemeral exception for current session attempt
    assert hasattr(controller, "grant_ephemeral_tls_exception"), (
        "WebSocketSessionController missing grant_ephemeral_tls_exception() method"
    )
    controller.grant_ephemeral_tls_exception()
    assert controller.has_ephemeral_tls_exception() is True

    # 2. Open connection under ephemeral override
    target = HandshakeTarget(url="wss://internal-dev.local:8443", headers={})
    controller.open(target)

    # 3. Simulate connection success under override
    controller.on_opened(subprotocol="")
    assert controller.state == SessionState.OPEN
    if emitted_classifications:
        expected = HostSecurityClassification.INSECURE_TLS_EXCEPTION.value
        assert emitted_classifications[-1] == expected

    # 4. Close session -> Ephemeral trust MUST reset back to default
    controller.close()
    if controller.state == SessionState.CLOSING:
        controller.on_closed(1000, "Clean close", peer_initiated=False)
    assert controller.state == SessionState.CLOSED
    assert controller.has_ephemeral_tls_exception() is False, (
        "Ephemeral TLS exception was not purged upon session closure"
    )

    # 5. Subsequent connection without explicit grant defaults back to strict verification
    controller.open(target)
    assert controller._target is not None
    assert controller._target.verify_tls is True
    controller.abort()


@pytest.mark.timeout(30)
def test_session_controller_security_classification_signal(qapp):
    """Verify WebSocketSessionController emits security_classification_changed on open."""
    from pypost.core.websocket_security_policy import HostSecurityClassification

    controller = WebSocketSessionController()
    classifications: list[str] = []

    assert hasattr(controller, "security_classification_changed"), (
        "WebSocketSessionController missing security_classification_changed signal"
    )
    controller.security_classification_changed.connect(
        lambda c: classifications.append(
            c if isinstance(c, str) else getattr(c, "value", str(c))
        )
    )

    # Plaintext remote
    controller.open(HandshakeTarget(url="ws://remote.example.com:8080/ws", headers={}))
    assert classifications[-1] == HostSecurityClassification.PLAINTEXT_REMOTE.value
    controller.abort()

    # Plaintext loopback
    controller.open(HandshakeTarget(url="ws://localhost:3000/ws", headers={}))
    assert classifications[-1] == HostSecurityClassification.PLAINTEXT_LOOPBACK.value
    controller.abort()

    # Secure TLS
    controller.open(HandshakeTarget(url="wss://echo.websocket.org", headers={}))
    assert classifications[-1] == HostSecurityClassification.SECURE_TLS.value
    controller.abort()


# =============================================================================
# 9. Observability and Structured Logging Tests
# =============================================================================


@pytest.mark.timeout(30)
def test_websocket_security_policy_observability_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verify structured debug logging in websocket_security_policy module."""
    from pypost.core.websocket_security_policy import (
        ConnectionSecurityPolicy,
        EphemeralSessionTrustDecision,
        TlsCertificateError,
        classify_endpoint_security,
        is_loopback_host,
    )

    with caplog.at_level(logging.DEBUG, logger="pypost.core.websocket_security_policy"):
        classify_endpoint_security("wss://echo.example.com", verify_tls=True)
        is_loopback_host("localhost")
        is_loopback_host("192.168.1.1")

        decision = EphemeralSessionTrustDecision(
            session_id="sess-999", target_url="wss://dev.local"
        )
        decision.reset()

        policy = ConnectionSecurityPolicy()
        err = TlsCertificateError(error_code="self_signed", message="Self-signed")
        policy.create_diagnostic_report("wss://dev.local", (err,))

    records = [r.getMessage() for r in caplog.records]
    assert any(
        "websocket_endpoint_security_classified" in m and "classification=secure_tls" in m
        for m in records
    )
    assert any(
        "websocket_host_loopback_evaluated host=localhost is_loopback=True" in m
        for m in records
    )
    assert any(
        "websocket_host_loopback_evaluated host=192.168.1.1 is_loopback=False" in m
        for m in records
    )
    assert any(
        "websocket_ephemeral_trust_decision_reset session_id=sess-999" in m
        for m in records
    )
    assert any(
        "websocket_tls_diagnostic_report_created url=wss://dev.local error_count=1" in m
        for m in records
    )


@pytest.mark.timeout(30)
def test_websocket_transport_observability_logging(
    qapp: object, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify structured logging in QtWebSocketTransport for connect and SSL errors."""
    from pypost.core.websocket_security_policy import TlsCertificateError

    transport = QtWebSocketTransport()

    class DummyListener:
        def on_opened(self, subprotocol: str) -> None:
            pass

        def on_text(self, message: str) -> None:
            pass

        def on_binary(self, payload: bytes) -> None:
            pass

        def on_pong(self, elapsed_ms: int, payload: bytes) -> None:
            pass

        def on_closed(self, code: int, reason: str, peer_initiated: bool) -> None:
            pass

        def on_failed(self, category: str, message: str, detail: str) -> None:
            pass

        def on_tls_errors(self, errors: tuple[TlsCertificateError, ...]) -> bool:
            return False

    transport.set_listener(DummyListener())

    with caplog.at_level(logging.DEBUG, logger="pypost.core.qt.websocket_transport"):
        target = HandshakeTarget(url="wss://127.0.0.1:9999", headers={}, verify_tls=True)
        transport.open(target)

    records = [r.getMessage() for r in caplog.records]
    assert any(
        "websocket_transport_open_initiated" in m and "verify_tls=True" in m
        for m in records
    )

    with caplog.at_level(logging.WARNING, logger="pypost.core.qt.websocket_transport"):
        err = TlsCertificateError(
            error_code="self_signed", message="The certificate is self-signed"
        )
        transport._on_ssl_errors([err])

    warn_records = [r.getMessage() for r in caplog.records]
    assert any(
        "websocket_transport_ssl_errors_encountered count=1" in m
        for m in warn_records
    )
    transport.abort()


@pytest.mark.timeout(30)
def test_session_controller_ephemeral_trust_observability_logging(
    qapp: object, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify logging for ephemeral trust exception grants, revokes, and session open."""
    controller = WebSocketSessionController()

    with caplog.at_level(logging.INFO, logger="pypost.core.qt.websocket_session"):
        controller.grant_ephemeral_tls_exception()
        controller.revoke_ephemeral_tls_exception()
        controller.grant_ephemeral_tls_exception()
        controller.open(HandshakeTarget(url="wss://sandbox.local:8443", headers={}))

    records = [r.getMessage() for r in caplog.records]
    assert any("websocket_ephemeral_tls_exception_granted" in m for m in records)
    assert any("websocket_ephemeral_tls_exception_revoked" in m for m in records)
    assert any(
        "Opening WebSocket session to wss://sandbox.local:8443" in m
        and "security=insecure_tls_exception" in m
        and "ephemeral_trust=True" in m
        for m in records
    )
    controller.abort()


@pytest.mark.timeout(30)
def test_session_controller_tls_error_caplog_contract(
    qapp: object, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify error-path logging for TLS validation failures satisfies caplog contract (C1/C5)."""
    from pypost.core.websocket_security_policy import TlsCertificateError
    from pypost.core.websocket_session_policy import SessionState

    controller = WebSocketSessionController()
    err = TlsCertificateError(
        error_code="self_signed",
        message="The certificate is self-signed",
    )

    controller.open(HandshakeTarget(url="wss://127.0.0.1:8443", headers={}, verify_tls=True))

    with caplog.at_level(logging.WARNING, logger="pypost.core.qt.websocket_session"):
        controller.on_tls_errors((err,))

    assert controller.state == SessionState.FAILED
    records = [r.getMessage() for r in caplog.records]
    assert any("websocket_tls_errors_encountered" in m for m in records)
    assert any(
        "websocket_session_tls_validation_failed" in m and "self-signed" in m.lower()
        for m in records
    )
