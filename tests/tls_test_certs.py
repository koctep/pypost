"""Ephemeral TLS test certificate profiles for offline WebSocket harness (PYPOST-1142).

Generates in-memory X.509 certificates for scripted ``wss://`` test servers without
external OpenSSL CLI dependencies. Profiles cover common TLS validation failure modes
used by PYPOST-1131 transport and session policy tests.
"""

from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum, auto

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from PySide6.QtNetwork import QSsl, QSslCertificate, QSslKey

logger = logging.getLogger(__name__)


class TlsCertProfile(Enum):
    """Supported TLS certificate profiles for scripted test servers."""

    SELF_SIGNED = auto()
    EXPIRED = auto()
    HOSTNAME_MISMATCH = auto()


@dataclass(frozen=True)
class TlsTestCertificate:
    """Generated certificate material for a single TLS test profile."""

    profile: TlsCertProfile
    certificate: QSslCertificate
    private_key: QSslKey
    cert_pem: bytes
    key_pem: bytes


def _build_x509_certificate(
    *,
    common_name: str,
    dns_names: tuple[str, ...],
    ip_addresses: tuple[ipaddress.IPv4Address | ipaddress.IPv6Address, ...],
    not_valid_before: datetime,
    not_valid_after: datetime,
    self_signed: bool = True,
) -> tuple[bytes, bytes]:
    """Build PEM-encoded certificate and private key bytes."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    issuer = subject if self_signed else subject

    san_entries: list[x509.GeneralName] = []
    for dns_name in dns_names:
        san_entries.append(x509.DNSName(dns_name))
    for ip_addr in ip_addresses:
        san_entries.append(x509.IPAddress(ip_addr))

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
    )
    if san_entries:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )

    certificate = builder.sign(private_key, hashes.SHA256())
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def build_tls_test_certificate(profile: TlsCertProfile) -> TlsTestCertificate:
    """Generate an ephemeral Qt-compatible certificate for the requested profile."""
    now = datetime.now(timezone.utc)

    if profile == TlsCertProfile.SELF_SIGNED:
        cert_pem, key_pem = _build_x509_certificate(
            common_name="localhost",
            dns_names=("localhost",),
            ip_addresses=(ipaddress.IPv4Address("127.0.0.1"),),
            not_valid_before=now - timedelta(days=1),
            not_valid_after=now + timedelta(days=365),
        )
    elif profile == TlsCertProfile.EXPIRED:
        cert_pem, key_pem = _build_x509_certificate(
            common_name="localhost",
            dns_names=("localhost",),
            ip_addresses=(ipaddress.IPv4Address("127.0.0.1"),),
            not_valid_before=now - timedelta(days=730),
            not_valid_after=now - timedelta(days=1),
        )
    elif profile == TlsCertProfile.HOSTNAME_MISMATCH:
        cert_pem, key_pem = _build_x509_certificate(
            common_name="mismatch.example.com",
            dns_names=("mismatch.example.com",),
            ip_addresses=(),
            not_valid_before=now - timedelta(days=1),
            not_valid_after=now + timedelta(days=365),
        )
    else:
        raise ValueError(f"Unsupported TLS certificate profile: {profile}")

    certificate = QSslCertificate(cert_pem)
    private_key = QSslKey(key_pem, QSsl.KeyAlgorithm.Rsa, QSsl.EncodingFormat.Pem)
    if certificate.isNull() or private_key.isNull():
        raise RuntimeError(f"Failed to load generated TLS certificate for profile {profile.name}")

    logger.debug(
        "tls_test_certificate_generated profile=%s subject=%s",
        profile.name,
        certificate.subjectDisplayName(),
    )
    return TlsTestCertificate(
        profile=profile,
        certificate=certificate,
        private_key=private_key,
        cert_pem=cert_pem,
        key_pem=key_pem,
    )
