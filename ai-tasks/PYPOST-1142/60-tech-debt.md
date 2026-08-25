# PYPOST-1142: Technical Debt Analysis

**Verdict:** Live TLS test server fixture with three certificate profiles (`SELF_SIGNED`, `EXPIRED`, `HOSTNAME_MISMATCH`), pytest fixtures, and 9 harness tests meet requirements and Definition of Done. All targeted tests pass with explicit timeout markers. Plaintext default unchanged.
**SAFE TO CLOSE.** Follow-up items below are non-blocking enhancements.

Scope reviewed:
- `tests/tls_test_certs.py` (`TlsCertProfile`, `TlsTestCertificate`, `build_tls_test_certificate`)
- `tests/websocket_echo_server.py` (optional `tls_profile`, `is_tls`, `wss://` URL)
- `tests/conftest.py` (`wss_test_server`, `wss_test_server_expired`, `wss_test_server_hostname_mismatch`)
- `tests/test_websocket_tls_echo_server.py` (9 tests)
- `doc/dev/websocket_test_harness.md` (TLS section)

---

## Shortcuts Taken

1. **Harness-Only Verification Bypass for Echo Tests**:
   - TLS echo tests configure `QSslSocket.PeerVerifyMode.VerifyNone` directly on `QWebSocket` clients rather than routing through `QtWebSocketTransport` / `WebSocketSessionController`.
   - *Rationale:* This task scopes to the WS-11 harness; transport/session live-matrix integration can be added in a follow-up without coupling certificate generation to production adapters.
2. **RSA 2048 Ephemeral Keys Per Profile Invocation**:
   - Each `build_tls_test_certificate()` call generates a fresh RSA key pair.
   - *Rationale:* Simple, deterministic, and fast enough for CI (~milliseconds). Caching keys across tests is unnecessary at current scale.
3. **Loopback-Only Hostname Mismatch Simulation**:
   - Hostname mismatch is exercised by presenting a cert for `mismatch.example.com` while connecting to `wss://127.0.0.1:<port>`.
   - *Rationale:* Keeps the harness offline and avoids DNS or `/etc/hosts` dependencies.

---

## Code Quality Issues

1. **No Shared Client Helper in Production Transport Layer**:
   - `_open_wss_client()` lives in the test module only.
   - *Improvement:* Future transport integration tests could reuse `QtWebSocketTransport` with the live server fixtures instead of raw `QWebSocket`.
2. **Profile Enum Not Parametrized Fixture**:
   - Three separate pytest fixtures (`wss_test_server`, `wss_test_server_expired`, `wss_test_server_hostname_mismatch`) instead of a single parametrized fixture.
   - *Improvement:* A `@pytest.fixture(params=[...])` `wss_test_server` could reduce fixture boilerplate if more profiles are added.

---

## Missing Tests

| Scenario | Status | Notes |
| -------- | ------ | ----- |
| TLS server startup and `wss://` URL | **Present** | `test_tls_server_startup_and_wss_url` |
| Self-signed rejection (default verify) | **Present** | Parametrized rejection test |
| Expired rejection | **Present** | Parametrized rejection test |
| Hostname mismatch rejection | **Present** | Parametrized rejection test |
| Text echo over `wss://` (verify none) | **Present** | `test_tls_self_signed_echo_with_verify_none` |
| Binary echo over `wss://` | **Present** | `test_tls_binary_echo_with_verify_none` |
| Fixture lifecycle (self-signed) | **Present** | `test_wss_test_server_fixture_lifecycle` |
| Fixture lifecycle (expired) | **Present** | `test_wss_test_server_fixture_parametrized_profile` |
| Live matrix via `QtWebSocketTransport` | Optional (TD-1) | Deferred — use harness fixtures in transport integration follow-up |
| Untrusted CA hierarchy (intermediate) | Out of Scope | FU-6 custom CA trust store |
| mTLS client certificate | Out of Scope | Enterprise feature |

### Timeout Marker Review
- **BLOCKER Check**: All 9 tests in `tests/test_websocket_tls_echo_server.py` declare `pytestmark = pytest.mark.timeout(15)` and per-function `@pytest.mark.timeout(10)`.
- **Result**: **NO BLOCKER** — 100% compliant with `do-testing` requirements.

---

## Performance Concerns

1. **RSA Key Generation per Certificate Build**:
   - Generating 2048-bit RSA keys adds minor CPU per test file run.
   - *Mitigation:* Acceptable for 9 tests (~4s total). Profile caching can be added if the matrix grows significantly.
2. **TLS Handshake Latency**:
   - Each rejection test waits up to 5s via `wait_until()` for SSL errors.
   - *Mitigation:* Errors typically arrive within one event-loop cycle; total suite wall time remains under 5s for TLS file.

---

## Follow-up Tasks

### Technical Debt Improvements (Non-blocking)
1. **TD-1 (Low)**: Add live `QtWebSocketTransport` / `WebSocketSessionController` integration tests using `wss_test_server` fixtures to close the synthesis gap noted in PYPOST-1131 tech debt.
2. **TD-2 (Low)**: Add `UNTRUSTED_CA` profile with a non-self-signed but untrusted intermediate chain when FU-6 custom CA testing is prioritized.

---

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Harness-only `VerifyNone` on raw clients is intentional test scope boundary |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | **None** |
| Acceptance gaps vs DoD | **None** |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1142.
