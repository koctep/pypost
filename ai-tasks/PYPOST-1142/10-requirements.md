# PYPOST-1142: WS — live TLS test server fixture with multi-cert profiles

## Goals

Epic [PYPOST-1123](https://pypost.atlassian.net/browse/PYPOST-1123) (WebSocket Protocol Support) delivered TLS policy and transport security in [PYPOST-1131](https://pypost.atlassian.net/browse/PYPOST-1131) (WS-8). That work intentionally deferred live `wss://` socket testing against a matrix of certificate failure modes to keep CI fast and avoid external OpenSSL CLI dependencies (see `ai-tasks/PYPOST-1131/60-tech-debt.md`).

This task closes that follow-up by extending the WS-11 in-process test harness ([PYPOST-1129](https://pypost.atlassian.net/browse/PYPOST-1129)) so developers and downstream stories can run **live, offline, end-to-end TLS handshake validation** against scripted loopback servers presenting self-signed, expired, and hostname-mismatch certificates.

**Implementation language:** Python (test infrastructure in the existing PyPost / PySide6 codebase; no production code changes).

## User Stories

- As a **test engineer** validating WebSocket TLS policy, I want a live `wss://` loopback server with selectable certificate profiles, so that transport and session tests exercise real Qt/OpenSSL handshake failures instead of only mocked `TlsCertificateError` fixtures.
- As a **developer** writing integration tests for `QtWebSocketTransport` and `WebSocketSessionController`, I want pytest fixtures that start a secure echo server on an ephemeral port, so that I can assert rejection and override lifecycles without external network or manual certificate files.
- As a **maintainer** of the WS-11 harness, I want plaintext (`ws://`) behavior unchanged by default, so that existing harness tests and downstream consumers do not regress.

## Definition of Done

The task is considered done when:

1. **Live TLS server mode**
   - `ScriptedWebSocketServer` accepts an optional TLS certificate profile and starts in `QWebSocketServer.SslMode.SecureMode` when configured.
   - The server exposes a `wss://127.0.0.1:<port>` URL on the same ephemeral loopback binding used for plaintext mode.

2. **Multi-cert profiles**
   - At minimum three profiles are available: **self-signed**, **expired**, and **hostname mismatch** (certificate SAN/CN does not match the loopback connection host).

3. **Pytest fixtures**
   - Function-scoped fixtures in `tests/conftest.py` yield running secure servers for each profile (default self-signed plus dedicated expired and hostname-mismatch fixtures).

4. **Automated verification**
   - Tests assert default peer verification rejects each profile with the expected diagnostic category.
   - Tests assert echo behavior works over `wss://` when verification is disabled for harness-only connections.
   - Every new test declares explicit `pytest.mark.timeout(...)`.

5. **Quality gates**
   - Targeted harness tests and `make lint` pass.
   - Developer documentation updated for TLS profiles and fixtures.

## Task Description

### Problem

`ScriptedWebSocketServer` currently binds only in `NonSecureMode` (`ws://`). PYPOST-1131 unit tests synthesize TLS failure scenarios via structured fixtures and mock listeners. Downstream transport integration tests cannot yet validate live handshake rejection against dynamically generated certificates.

### Scope

**In scope:**

- Ephemeral in-memory X.509 certificate generation for test profiles (`tests/tls_test_certs.py`).
- TLS mode on `ScriptedWebSocketServer` (`tls_profile` constructor parameter).
- `wss_test_server` pytest fixtures.
- Test suite `tests/test_websocket_tls_echo_server.py`.
- Developer documentation update in `doc/dev/websocket_test_harness.md`.

**Out of scope:**

- Production code under `pypost/`.
- Custom CA trust store loading (FU-6 / enterprise settings).
- Mutual TLS (mTLS) client certificates.
- Changes to `ServerBehavior` scripted behavior semantics beyond TLS transport mode.

### Constraints and assumptions

- Certificates are generated in-process via the existing `cryptography` dependency; no checked-in PEM files or OpenSSL CLI.
- Servers bind to `127.0.0.1:0` only; hostname-mismatch profile is validated by connecting to `127.0.0.1` while the certificate names `mismatch.example.com`.
- Default harness construction remains plaintext (`ws://`) for backward compatibility.

## Q&A

**Q: Why not add TLS to `ServerBehaviorConfig`?**
A: TLS is a transport concern orthogonal to scripted message behaviors. A dedicated constructor parameter keeps benchmark and behavior configuration separate, matching the `max_history` pattern from PYPOST-1140.

**Q: How does this relate to PYPOST-1131?**
A: PYPOST-1131 implemented domain policy and transport SSL configuration. This task supplies the missing live test server matrix referenced as follow-up `PYPOST-1142` in `ai-tasks/PYPOST-1131/60-tech-debt.md`.
