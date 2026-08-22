# PYPOST-1131: Technical Debt Analysis

## Shortcuts Taken

1. **In-Memory Binary Ephemeral Bypass (`VerifyNone`)**:
   - In accordance with RFC PYPOST-1124 (D-12), when an ephemeral trust exception is granted by the operator for a test session, the transport sets `QSslSocket.PeerVerifyMode.VerifyNone` on the socket's `QSslConfiguration` prior to opening the connection.
   - This cleanly eliminates blanket `ignoreSslErrors()` calls and preserves the non-persistence invariant. However, granting an exception bypasses all certificate validation errors for that specific session attempt at once (e.g., self-signed, expired, hostname mismatch) rather than enabling granular, error-by-error whitelisting. This matches standard developer testing tooling behavior prior to full enterprise CA management (FU-6).
2. **Synthesized TLS Error Diagnostics in Unit Tests vs Live Multi-Certificate Test Server Matrix**:
   - Integration and unit tests verify `QtWebSocketTransport` error parsing and `WebSocketSessionController` lifecycles using structured `TlsCertificateError` fixtures and mock listeners.
   - Live socket testing against a local matrix of dynamically generated X.509 certificates (e.g., expired certificates, untrusted CA hierarchies, SAN mismatches, wildcard certificates) was synthesized via unit tests to avoid external OpenSSL CLI dependencies, dynamic port contention, and slow multi-process test setups during standard CI runs (< 0.2s suite runtime).
3. **Guarded Digest Extraction Fallback**:
   - In `QtWebSocketTransport._on_ssl_errors`, SHA-256 fingerprint extraction from `QSslCertificate.digest()` uses a guarded `try...except Exception` block that falls back to an empty string if Qt's underlying OpenSSL backend is unavailable or uninitialized in certain minimal headless environments.

## Code Quality Issues

1. **Heuristic Error Code Mapping in Transport Adapter**:
   - In `QtWebSocketTransport._on_ssl_errors`, error codes are extracted from `QSslError.error()` enum names when available, with string pattern fallbacks (`"self_signed"`, `"host_mismatch"`, `"expired"`) when operating on string representations.
   - While robust across PySide6 versions and mock objects, centralizing all `QSslError.SslError` Qt enum values in a dedicated domain mapping table in `pypost/core/websocket_security_policy.py` would provide even tighter typed mapping.
2. **IPv6 Scope / Zone Identifier Parsing**:
   - `is_loopback_host` strips outer brackets (`[::1] -> ::1`) and parses the IP using `ipaddress.ip_address()`.
   - If an IPv6 host string includes a scope identifier (e.g. `fe80::1%lo0` or `[::1%1]`), `ipaddress.ip_address()` raises a `ValueError` which is safely caught and returns `False`. Explicitly stripping `%<scope_id>` before IP parsing would further enhance IPv6 scope handling.
3. **Session Controller Security Coordination**:
   - `WebSocketSessionController` in `pypost/core/qt/websocket_session.py` coordinates ephemeral trust decisions and security classification signal emissions directly.
   - As additional connection security policies are added in future iterations (e.g., mTLS client certificates, proxy authentication), extracting this logic into a dedicated session security coordinator helper would keep `WebSocketSessionController` even more focused.

## Missing Tests

1. **Current Test Suite Coverage**:
   - All 19 tests in `tests/test_websocket_tls_policy.py` pass with 100% success.
   - All tests include explicit timeout markers (`pytestmark = pytest.mark.timeout(30)` and `@pytest.mark.timeout(30)`), strictly adhering to the `do-testing` skill requirements.
   - All 119 WebSocket test cases across `tests/test_websocket_*.py` pass cleanly.
2. **Pre-existing Test Failures**:
   - None. The repository test suite and static analysis gates pass with zero pre-existing failures.
3. **Future Test Scenarios (Deferred to Downstream Tasks / Follow-ups)**:
   - **FU-6 Custom CA Trust Store Integration Tests**: Testing custom CA certificate bundle loading (`QSslConfiguration.setCaCertificates()`) and custom root trust stores.
   - **Mutual TLS (mTLS) Client Certificate Tests**: Testing client certificate and private key negotiation over `wss://`.
   - **Internationalized Domain Names (IDN) / Punycode Loopback**: Adding explicit test fixtures for punycode domains (e.g. `xn--...localhost`).
   - **GUI Presenter & Warning Badge Widget Tests**: Testing UI toolbar badge rendering for `PLAINTEXT_REMOTE`, `SECURE_TLS`, and `INSECURE_TLS_EXCEPTION` in GUI tasks (WS-4 / WS-5 / WS-6).

## Performance Concerns

1. **Zero Overhead on Frame Streaming**:
   - Host classification and endpoint security classification (`classify_endpoint_security()`, `is_loopback_host()`) occur once per connection open request.
   - During active streaming of messages and frame transfers, zero security policy evaluation overhead is incurred.
2. **Negligible In-Memory Footprint**:
   - `EphemeralSessionTrustDecision` maintains only active session identifiers, timestamps, and boolean flags in volatile memory.
   - All trust decision state is purged immediately upon session disconnection or close, ensuring zero memory accumulation over long-running application lifecycles.

## Follow-up Tasks

The following follow-up tasks are identified for future development:
- `PYPOST-1142`: Add live TLS test server fixture with multi-cert profiles to echo server (3 SP).
  - Add persistent user-managed custom root CA certificates, enterprise proxy certificates, and custom trust stores in application settings without requiring ephemeral security bypasses.
- **PYPOST-1130 (WS-4 / WS-5): UI Integration of Connection Security Badges & Prompts**:
  - Connect `security_classification_changed` and `tls_errors_raised` signals from `WebSocketSessionController` to the WebSocket Editor toolbar.
  - Display security indicators (Lock icon for `SECURE_TLS`, Alert warning banner for `PLAINTEXT_REMOTE`, Warning badge for `INSECURE_TLS_EXCEPTION`) and present interactive ephemeral trust confirmation dialogs.
- **mTLS Client Certificate Negotiation**:
  - Add client certificate and private key configuration to `QSslConfiguration` for mutual TLS authentication on enterprise endpoints.
