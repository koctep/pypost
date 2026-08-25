"""Tests for TLS-enabled ScriptedWebSocketServer and wss_test_server fixture (PYPOST-1142).

Asserts live ``wss://`` startup, multi-cert profile generation, handshake rejection
for self-signed / expired / hostname-mismatch certificates, and echo behavior when
verification is bypassed for harness-only connections.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QByteArray, QUrl
from PySide6.QtNetwork import QSslConfiguration, QSslSocket
from PySide6.QtWebSockets import QWebSocket

from pypost.agent.ui_wait import wait_until
from tests.tls_test_certs import TlsCertProfile, build_tls_test_certificate
from tests.websocket_echo_server import (
    ScriptedWebSocketServer,
    ServerBehavior,
    ServerBehaviorConfig,
)

pytestmark = pytest.mark.timeout(15)


def _open_wss_client(
    url: str,
    *,
    verify_tls: bool = True,
) -> tuple[QWebSocket, list[object]]:
    """Open a QWebSocket client against ``url`` and collect SSL errors."""
    client = QWebSocket()
    ssl_errors: list[object] = []
    client.sslErrors.connect(lambda errors: ssl_errors.extend(errors))

    if not verify_tls:
        ssl_config = QSslConfiguration.defaultConfiguration()
        ssl_config.setPeerVerifyMode(QSslSocket.PeerVerifyMode.VerifyNone)
        client.setSslConfiguration(ssl_config)

    client.open(QUrl(url))
    return client, ssl_errors


def _ssl_error_messages(errors: list[object]) -> list[str]:
    return [getattr(error, "errorString", lambda: str(error))() for error in errors]


@pytest.mark.timeout(10)
def test_tls_server_startup_and_wss_url(qapp) -> None:
    """TLS server starts in SecureMode and exposes a wss:// loopback URL."""
    server = ScriptedWebSocketServer(tls_profile=TlsCertProfile.SELF_SIGNED)
    server.start()
    try:
        assert server.is_tls is True
        assert server.tls_profile == TlsCertProfile.SELF_SIGNED
        assert server.tls_certificate is not None
        assert server.url.startswith("wss://127.0.0.1:")
        assert server.port > 0
    finally:
        server.stop()


@pytest.mark.timeout(10)
def test_tls_certificate_profiles_generate_distinct_material() -> None:
    """Each TLS profile produces distinct certificate subjects and validity windows."""
    self_signed = build_tls_test_certificate(TlsCertProfile.SELF_SIGNED)
    expired = build_tls_test_certificate(TlsCertProfile.EXPIRED)
    mismatch = build_tls_test_certificate(TlsCertProfile.HOSTNAME_MISMATCH)

    assert "localhost" in self_signed.certificate.subjectDisplayName().lower()
    assert "localhost" in expired.certificate.subjectDisplayName().lower()
    assert "mismatch.example.com" in mismatch.certificate.subjectDisplayName().lower()
    assert expired.certificate.expiryDate() < self_signed.certificate.expiryDate()


@pytest.mark.timeout(10)
@pytest.mark.parametrize(
    "profile,expected_fragment",
    [
        (TlsCertProfile.SELF_SIGNED, "self-signed"),
        (TlsCertProfile.EXPIRED, "expired"),
        (TlsCertProfile.HOSTNAME_MISMATCH, "host name"),
    ],
)
def test_tls_profile_rejects_default_verification(
    qapp,
    profile: TlsCertProfile,
    expected_fragment: str,
) -> None:
    """Default peer verification rejects each scripted TLS certificate profile."""
    server = ScriptedWebSocketServer(tls_profile=profile)
    server.start()
    client, ssl_errors = _open_wss_client(server.url, verify_tls=True)
    try:
        wait_until(
            lambda: bool(ssl_errors) or client.state().name in {"UnconnectedState", "ClosingState"},
            timeout=5.0,
            message=f"Expected TLS rejection for profile {profile.name}",
        )
        messages = " ".join(_ssl_error_messages(ssl_errors)).lower()
        assert expected_fragment in messages
        assert not client.isValid()
    finally:
        client.abort()
        server.stop()


@pytest.mark.timeout(10)
def test_tls_self_signed_echo_with_verify_none(qapp) -> None:
    """Self-signed TLS server echoes text when client verification is disabled."""
    server = ScriptedWebSocketServer(
        config=ServerBehaviorConfig(behavior=ServerBehavior.ECHO),
        tls_profile=TlsCertProfile.SELF_SIGNED,
    )
    server.start()
    received_texts: list[str] = []
    client, _ssl_errors = _open_wss_client(server.url, verify_tls=False)
    client.textMessageReceived.connect(received_texts.append)
    try:
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="TLS client failed to connect with verify_tls=False",
        )
        client.sendTextMessage("secure echo")
        wait_until(
            lambda: received_texts == ["secure echo"],
            timeout=5.0,
            message="TLS echo server did not return text message",
        )
        assert server.received_text_messages == ["secure echo"]
    finally:
        client.close()
        client.abort()
        server.stop()


@pytest.mark.timeout(10)
def test_tls_binary_echo_with_verify_none(qapp) -> None:
    """TLS server echoes binary frames when verification is disabled."""
    server = ScriptedWebSocketServer(
        config=ServerBehaviorConfig(behavior=ServerBehavior.ECHO),
        tls_profile=TlsCertProfile.SELF_SIGNED,
    )
    server.start()
    received_binaries: list[bytes] = []
    client, _ssl_errors = _open_wss_client(server.url, verify_tls=False)
    client.binaryMessageReceived.connect(lambda payload: received_binaries.append(bytes(payload)))
    try:
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="TLS client failed to connect for binary echo",
        )
        payload = b"\x00\x01\x02\xfe\xff"
        client.sendBinaryMessage(QByteArray(payload))
        wait_until(
            lambda: received_binaries == [payload],
            timeout=5.0,
            message="TLS echo server did not return binary message",
        )
    finally:
        client.close()
        client.abort()
        server.stop()


@pytest.mark.timeout(10)
def test_wss_test_server_fixture_lifecycle(wss_test_server) -> None:
    """pytest fixture wss_test_server yields an active secure loopback server."""
    assert wss_test_server.is_listening
    assert wss_test_server.is_tls is True
    assert wss_test_server.tls_profile == TlsCertProfile.SELF_SIGNED
    assert wss_test_server.url.startswith("wss://127.0.0.1:")


@pytest.mark.timeout(10)
def test_wss_test_server_fixture_parametrized_profile(wss_test_server_expired) -> None:
    """Dedicated expired-profile fixture exposes the expected TLS profile."""
    assert wss_test_server_expired.is_tls is True
    assert wss_test_server_expired.tls_profile == TlsCertProfile.EXPIRED
    assert wss_test_server_expired.url.startswith("wss://127.0.0.1:")
