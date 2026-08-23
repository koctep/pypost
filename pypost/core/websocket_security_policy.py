"""Pure Qt-free domain logic and data structures for WebSocket TLS and connection security."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import ipaddress
import logging
from typing import Optional, Union
import urllib.parse

logger = logging.getLogger(__name__)


class HostSecurityClassification(str, Enum):
    """Security classification of a WebSocket endpoint transport."""

    SECURE_TLS = "secure_tls"
    INSECURE_TLS_EXCEPTION = "insecure_tls_exception"
    PLAINTEXT_REMOTE = "plaintext_remote"
    PLAINTEXT_LOOPBACK = "plaintext_loopback"


@dataclass(frozen=True)
class TlsCertificateError:
    """Detailed metadata for a single TLS certificate validation failure."""

    error_code: str
    message: str
    certificate_subject: str = ""
    certificate_issuer: str = ""
    certificate_fingerprint: str = ""
    expiry_date: Optional[datetime] = None


@dataclass(frozen=True)
class TlsDiagnosticReport:
    """Structured diagnostic report containing all TLS errors encountered."""

    errors: tuple[TlsCertificateError, ...]
    summary_message: str
    target_url: str
    target_host: str
    timestamp: datetime


@dataclass
class EphemeralSessionTrustDecision:
    """In-memory, non-persistent trust decision for an active session."""

    session_id: str
    target_url: str
    exception_granted: bool = False
    granted_at: Optional[datetime] = None

    def reset(self) -> None:
        """Purge exception grant on session termination."""
        logger.debug(
            "websocket_ephemeral_trust_decision_reset session_id=%s url=%s",
            self.session_id,
            self.target_url,
        )
        self.exception_granted = False
        self.granted_at = None


def is_loopback_host(host: str) -> bool:
    """Classify whether a given host name or IP string is a local loopback interface.

    Recognizes:
    - Case-insensitive "localhost", "localhost.localdomain"
    - Subdomains ending with ".localhost" per RFC 6761 (e.g. "sub.localhost")
    - IPv4 loopback network (127.0.0.0/8)
    - IPv6 loopback address (::1, [::1])
    """
    if not host:
        return False
    clean_host = host.strip().lower()
    if clean_host.startswith("[") and clean_host.endswith("]"):
        clean_host = clean_host[1:-1]
    if not clean_host:
        return False
    if clean_host in ("localhost", "localhost.localdomain") or clean_host.endswith(".localhost"):
        logger.debug("websocket_host_loopback_evaluated host=%s is_loopback=True", host)
        return True
    try:
        ip = ipaddress.ip_address(clean_host)
        res = ip.is_loopback
        logger.debug("websocket_host_loopback_evaluated host=%s is_loopback=%s", host, res)
        return res
    except ValueError:
        logger.debug("websocket_host_loopback_evaluated host=%s is_loopback=False", host)
        return False


def classify_endpoint_security(url: str, verify_tls: bool = True) -> HostSecurityClassification:
    """Determine the HostSecurityClassification for a target URL and TLS verification setting."""
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname or ""

    classification: HostSecurityClassification
    if scheme == "wss":
        if verify_tls:
            classification = HostSecurityClassification.SECURE_TLS
        else:
            classification = HostSecurityClassification.INSECURE_TLS_EXCEPTION
    elif scheme == "ws":
        if is_loopback_host(hostname):
            classification = HostSecurityClassification.PLAINTEXT_LOOPBACK
        else:
            classification = HostSecurityClassification.PLAINTEXT_REMOTE
    else:
        if is_loopback_host(hostname):
            classification = HostSecurityClassification.PLAINTEXT_LOOPBACK
        else:
            classification = HostSecurityClassification.PLAINTEXT_REMOTE

    from pypost.core.sensitive_text_sanitizer import sanitize_text
    logger.debug(
        "websocket_endpoint_security_classified url=%s verify_tls=%s classification=%s",
        sanitize_text(url),
        verify_tls,
        classification.value,
    )
    return classification


classify_host_security = classify_endpoint_security


def is_plaintext_warning_required(
    endpoint_or_classification: Union[str, HostSecurityClassification],
    verify_tls: bool = True,
) -> bool:
    """Return True if the target endpoint represents an unencrypted remote connection."""
    if isinstance(endpoint_or_classification, HostSecurityClassification):
        return endpoint_or_classification == HostSecurityClassification.PLAINTEXT_REMOTE
    classification = classify_endpoint_security(endpoint_or_classification, verify_tls=verify_tls)
    return classification == HostSecurityClassification.PLAINTEXT_REMOTE


class ConnectionSecurityPolicy:
    """Domain policy engine for WebSocket connection security."""

    @staticmethod
    def classify(url: str, verify_tls: bool = True) -> HostSecurityClassification:
        """Classify security posture of a target URL."""
        return classify_endpoint_security(url, verify_tls=verify_tls)

    @staticmethod
    def is_loopback(host: str) -> bool:
        """Check if host is a loopback address."""
        return is_loopback_host(host)

    @staticmethod
    def is_plaintext_warning_required(
        url_or_classification: Union[str, HostSecurityClassification],
        verify_tls: bool = True,
    ) -> bool:
        """Check if plaintext warning banner should be displayed."""
        return is_plaintext_warning_required(url_or_classification, verify_tls=verify_tls)

    @staticmethod
    def create_diagnostic_report(
        url: str,
        errors: tuple[TlsCertificateError, ...],
        timestamp: Optional[datetime] = None,
    ) -> TlsDiagnosticReport:
        """Construct structured TlsDiagnosticReport from collection of certificate errors."""
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or parsed.netloc or ""
        ts = timestamp if timestamp is not None else datetime.now(timezone.utc)
        if not errors:
            summary = "TLS validation succeeded without errors"
        else:
            descriptions = [e.message for e in errors if e.message]
            summary = f"TLS validation failed: {'; '.join(descriptions)}"
        logger.debug(
            "websocket_tls_diagnostic_report_created url=%s error_count=%d",
            url,
            len(errors),
        )
        return TlsDiagnosticReport(
            errors=errors,
            summary_message=summary,
            target_url=url,
            target_host=host,
            timestamp=ts,
        )
