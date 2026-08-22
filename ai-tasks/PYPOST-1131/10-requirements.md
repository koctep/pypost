# PYPOST-1131: WS-8 TLS and connection-security policy

## Goals

Real-time WebSocket communication over `wss://` regularly carries sensitive authentication credentials, private session tokens, and business-critical data payloads. If TLS verification failures are ignored, suppressed, or handled insecurely, users become vulnerable to Man-in-the-Middle (MitM) attacks, certificate spoofing, and credential interception. Conversely, when developers intentionally test against local, staging, or private sandbox environments utilizing self-signed or custom certificates, vague failure notices hinder debugging and create friction.

The primary goals of this task are:
- **Secure by Default**: Guarantee that all `wss://` connections enforce full TLS certificate-chain and hostname verification by default, rejecting untrusted, self-signed, expired, or mismatched certificates before a session reaches `Open`.
- **Actionable Diagnostic Transparency**: Provide clear, specific certificate verification error messages (e.g. self-signed certificate, hostname mismatch, expired validity, untrusted root authority) rather than ambiguous or generic connection failures.
- **Strictly Ephemeral Trust Overrides**: When an operator deliberately accepts an untrusted certificate exception for testing, restrict that override to the specific active session only and enforce a strict non-persistence guarantee where exceptions are never written to disk, collection JSON files, or application settings.
- **Visible Insecurity Warnings for Plaintext Transports**: Ensure that unencrypted `ws://` connections to remote, non-loopback hosts present a persistent, prominent plaintext warning to make insecure transport choices explicit, while avoiding false alerts on local development loopback addresses (`localhost`, `127.0.0.1`, `::1`).
- **Static Codebase Security Guardrail**: Enforce an automated architectural guard test ensuring that blanket TLS verification bypasses (specifically `ignoreSslErrors(`) cannot be introduced into production code under `pypost/`.

**Implementation language**: Python (targeting Python 3.11+ and the existing PySide6 6.11+ runtime stack; strict separation of security policy and headless transport verification).

## User Stories

- **As an API developer testing secure services (`wss://`)**, I want my WebSocket connections to verify server certificates strictly by default, so that I am protected from credential leakage and network eavesdropping.
- **As an API developer diagnosing a staging endpoint with a self-signed or private certificate**, I want to see the exact certificate validation errors rather than a generic failure message, so that I can immediately understand why TLS verification failed.
- **As an API developer who needs to proceed with testing against a known private sandbox**, I want to temporarily allow a certificate exception for my current test session only, without that insecure choice being permanently saved to disk or affecting other collections and future sessions.
- **As a security auditor / compliance reviewer**, I want to verify that certificate overrides are never persisted to disk files (settings or collections) and that blanket SSL verification bypasses are prohibited in production source code by automated tests.
- **As an API developer connecting over plaintext `ws://` to an external host**, I want a clear, persistent warning that my connection is unencrypted, so that I am aware of the risk of transmitting sensitive tokens across public networks.
- **As a developer working on local services (`localhost`, `127.0.0.1`, `::1`)**, I want unencrypted local connections to connect smoothly without redundant remote-plaintext security warnings, so that my local development workflow remains noise-free.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Secure-by-Default TLS Enforcement (`wss://`)**:
   Connecting to any `wss://` endpoint enforces strict TLS certificate-chain and hostname verification. Self-signed certificates, expired certificates, untrusted root authorities, and hostname mismatches are rejected by default, preventing the session from transitioning to `Open`.
2. **Specific Certificate Error Diagnostics**:
   When a TLS validation error occurs, the exact certificate failure reasons (e.g. self-signed certificate, hostname mismatch, certificate expired) are captured and surfaced directly to the operator, rather than reporting a generic "connection failed" error.
3. **Per-Session Non-Persistent Exception Lifecycles**:
   If a user elects to accept a certificate exception for a session, that override applies strictly to that single session instance. Under no circumstances is the exception written to disk. Post-session inspection of collection JSON files and application settings files asserts zero persistence of certificate exceptions.
4. **Persistent Plaintext Warning for Non-Loopback `ws://`**:
   Initiating an unencrypted `ws://` connection to any remote, non-loopback host displays a persistent plaintext security warning indicator alongside the connection status, alerting the user to unencrypted wire transmission.
5. **Loopback Exemption for Plaintext Warnings**:
   Connecting via `ws://` to standard local loopback addresses (`127.0.0.1`, `localhost`, `::1`, and equivalent local loopback bindings) does not trigger the remote plaintext security warning.
6. **Codebase Static Guardrail Against Blanket SSL Bypasses**:
   An automated static analysis / AST guard test fails if `ignoreSslErrors(` appears anywhere in production code under `pypost/`, ensuring that blanket SSL verification bypasses cannot regress into the codebase.
7. **Offline Hermetic Test Verification**:
   All TLS security behaviors—including default rejection, error extraction, per-session exception boundaries, zero disk leakage, and loopback detection—are validated with automated, offline tests using local test server fixtures.

## Task Description

PYPOST-1131 represents engineering story WS-8 (Wave 2) of Epic PYPOST-1123, establishing the TLS and connection-security policy designed in RFC PYPOST-1124 (specifically architectural sections A-13.8 and A-8.3 D-12).

This story builds on the transport abstraction delivered in WS-1 (PYPOST-1127) to ensure that security policies are strictly enforced across real-time WebSocket sessions.

### Scope

- **TLS Verification Policy**: Default configuration enforcing complete certificate-chain validation, root CA trust, and hostname verification for all secure (`wss://`) WebSocket connections.
- **TLS Diagnostics & Error Reporting**: Detailed extraction and propagation of specific certificate errors (e.g. certificate authority untrusted, self-signed, invalid validity dates, hostname mismatches).
- **Per-Session Trust Exception Management**: Ephemeral in-memory handling of certificate exceptions, defaulted to reject, with zero serialization to persistent storage.
- **Plaintext Warning Policy**: Classification of target hostnames into loopback vs. non-loopback to drive persistent security warning indicators for unencrypted `ws://` connections.
- **Static Guardrail**: Automated test checking the production source tree (`pypost/`) to enforce the prohibition of blanket `ignoreSslErrors(`.
- **Test Suite**: Automated unit and integration tests verifying secure-by-default rejection, detailed error propagation, ephemeral override limits, post-session on-disk state verification, and loopback classification.

### Out of Scope

- Certificate authority (CA) management GUI, custom trust store imports, or permanent certificate trust databases (tracked as follow-up FU-6).
- HTTP / REST TLS configuration modifications (existing HTTP client security policies remain untouched).
- UI composer, stream inspector, or sequence runner styling (handled in WS-4, WS-5, and WS-6).
- Sensitive variable masking within message payloads (covered in WS-7).

## Functional Requirements

- **FR-1: Default TLS Verification on `wss://`**:
  - The connection engine must mandate full TLS verification for all `wss://` targets.
  - The handshake must fail and abort if the peer certificate cannot be verified against the system trust store or if the certificate subject/SAN does not match the target hostname.
  - An untrusted or invalid connection must never transition to the `Open` state under default policy.
- **FR-2: Specific Certificate Error Extraction**:
  - The transport layer must capture all specific validation errors raised during the TLS handshake.
  - Errors must distinguish between categories such as: self-signed certificate, untrusted certificate authority, expired or not yet valid certificate, and hostname mismatch.
  - Error messages presented to the user or emitted via lifecycle events must include the concrete diagnostic strings.
- **FR-3: Ephemeral Per-Session Insecurity Override**:
  - The system must provide a mechanism to allow an explicit, per-session exception for certificate validation failures.
  - The decision must be reject-by-default: without explicit opt-in, the connection remains aborted.
  - When granted, the exception applies exclusively to the active session attempt and does not carry over to subsequent new connections, re-connections, or application restarts.
- **FR-4: Invariant of Zero Disk Persistence for Exceptions**:
  - Certificate exception flags, accepted fingerprints, or insecure bypasses must never be serialized into `Collection` JSON files, `WebSocketConnection` models, or `AppSettings`.
  - Closing a session or closing the application must completely purge all in-memory exception states.
- **FR-5: Loopback-Aware Plaintext Warning**:
  - When a target URL uses the unencrypted `ws://` scheme, the system must evaluate whether the host represents a local loopback interface.
  - Loopback targets (`localhost`, `127.0.0.1`, `::1`) must be classified as local/safe from remote wire snooping.
  - Non-loopback targets (e.g. `ws://api.example.com`, `ws://192.168.1.50`) must trigger a persistent plaintext warning state indicating unencrypted wire communication.
- **FR-6: Static Guardrail Against Insecure Symbols**:
  - Automated tests must inspect all Python files in `pypost/` to guarantee that `ignoreSslErrors(` does not appear in production code.

## Non-Functional Requirements

- **NFR-1: Security & Confidentiality**:
  - Default configurations must prioritize security and data confidentiality over convenience.
  - No secret tokens, credentials, or payloads may be transmitted over unverified TLS connections unless explicitly permitted by an ephemeral user decision.
  - Insecure decisions must leave zero traces on disk to prevent accidental long-term security posture degradation.
- **NFR-2: Clarity & Diagnostic Transparency**:
  - Security failures must be clearly distinguished from general transport/network failures (e.g. DNS failure, connection refused, connection reset).
  - Diagnostic error strings must directly guide the developer on what aspect of the certificate failed validation.
- **NFR-3: Reliability & State Isolation**:
  - Security states of one session must not leak into or affect any other concurrent or subsequent session.
  - Resetting or closing a session must deterministically clean up all temporary TLS state.
- **NFR-4: Testability & Automation**:
  - All TLS verification policies, failure modes, error extractions, and host classifications must be thoroughly testable in headless CI environments (`QT_QPA_PLATFORM=offscreen`) without external network access.

## Main Entities

- **ConnectionSecurityPolicy**: Business rules defining TLS certificate verification requirements, error handling behaviors, and plaintext warning triggers.
- **CertificateDiagnosticReport**: Structured diagnostic entity containing the specific list of TLS verification failure descriptions (e.g. self-signed, invalid hostname, expired).
- **EphemeralSessionTrustDecision**: In-memory, non-persistent decision record indicating whether an exception has been explicitly permitted for the current active session.
- **HostSecurityClassification**: Business classification of a target connection endpoint:
  - *Secure TLS*: `wss://` with verified certificate.
  - *Insecure TLS Exception*: `wss://` with an active ephemeral certificate exception.
  - *Plaintext Remote*: `ws://` to a remote/non-loopback destination (triggers warning).
  - *Plaintext Loopback*: `ws://` to a local loopback address (trusted local interface).

## User Scenarios

1. **Scenario 1: Successful Connection to Valid TLS Endpoint**:
   - User initiates a connection to `wss://echo.websocket.org`.
   - The remote server presents a valid certificate signed by a recognized CA matching the hostname.
   - The connection handshakes successfully, verifies TLS, and transitions to `Open` with no security warnings.
2. **Scenario 2: Connection Rejected on Self-Signed Certificate by Default**:
   - User initiates a connection to an internal test endpoint `wss://internal-dev.local` presenting a self-signed certificate.
   - Default TLS verification detects the untrusted certificate.
   - The connection is immediately aborted, never reaching `Open`.
   - The user is presented with a specific diagnostic message: `"The certificate is self-signed"`.
3. **Scenario 3: Connection Rejected on Hostname Mismatch**:
   - User initiates a connection to `wss://192.168.1.100` where the certificate was issued for `api.example.com`.
   - TLS validation identifies that the certificate subject does not match the request host.
   - The connection aborts in `Failed` state, displaying: `"The host name did not match any of the valid hosts for this certificate"`.
4. **Scenario 4: Temporary Ephemeral Exception Granted for Current Session**:
   - After a self-signed certificate rejection on a local test server, the developer explicitly chooses to proceed for this test session.
   - The connection is re-attempted with the ephemeral exception active; the session reaches `Open`.
   - The UI indicates that the session is running under an insecure certificate override.
   - After closing the session, inspection of collection data and settings files confirms that no certificate exception or bypass was saved to disk.
5. **Scenario 5: Exception Does Not Persist Across Sessions or Restarts**:
   - Following Scenario 4, the developer opens a new tab or restarts PyPost and attempts to connect to the same `wss://internal-dev.local` endpoint.
   - Because exceptions are strictly ephemeral and non-persistent, the new session rejects the self-signed certificate by default and requires explicit authorization again.
6. **Scenario 6: Plaintext Connection to Remote Host**:
   - User configures a WebSocket endpoint with `ws://remote-service.com:8080`.
   - The system identifies that `ws://` is used with a non-loopback host.
   - The session displays a persistent `plaintext` warning indicator, highlighting the risk of transmitting unencrypted credentials.
7. **Scenario 7: Plaintext Connection to Localhost**:
   - User configures a WebSocket endpoint with `ws://localhost:3000` or `ws://127.0.0.1:8000`.
   - The system recognizes the destination as a local loopback interface.
   - No remote-plaintext security warning is displayed, avoiding unnecessary noise.
8. **Scenario 8: Static Guard Test Fails on Blanket Bypass**:
   - A pull request introduces a blanket `ignoreSslErrors(` call into production code under `pypost/`.
   - Automated CI runs the static isolation test suite.
   - The guard test detects the forbidden symbol and fails the build with an explanatory architectural error.

## Q&A

| Question | Answer |
| --- | --- |
| Why is TLS certificate validation enabled by default without silent fallback? | Silent fallback or unverified TLS connections expose users to Man-in-the-Middle attacks and credential leakage. In accordance with RFC PYPOST-1124 (D-12), security by default ensures that insecure transport states are never entered silently. |
| Why must certificate errors be specific instead of generic "Connection Failed"? | Developers frequently test against development clusters and staging environments. Precise diagnostic strings (such as "self-signed certificate" or "hostname mismatch") allow developers to immediately identify the root cause without having to inspect external network traces. |
| Why are certificate exceptions strictly non-persistent? | Persisting certificate overrides to disk risks permanent security degradation and credential leakage if collection files are shared or if temporary exceptions are forgotten. In accordance with D-12, permanent certificate management is deferred to FU-6. |
| Why distinguish loopback addresses (`localhost`, `127.0.0.1`, `::1`) from remote hosts? | Local loopback traffic never leaves the host machine's network stack, making it safe from external wire-tapping. Suppressing plaintext warnings for loopback addresses avoids alert fatigue during local development while keeping warnings active for external networks. |
| Why is `ignoreSslErrors(` forbidden in production code? | Unconditional `ignoreSslErrors()` calls bypass all cryptographic validation indiscriminately. Mandating an automated static guard test ensures that secure defaults cannot be accidentally bypassed in production code. |
