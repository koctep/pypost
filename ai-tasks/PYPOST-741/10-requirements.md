# PYPOST-741: Redact resolved URLs in HTTP client ERROR logs

## Goals

PyPost operators configure HTTP requests whose URLs may include environment-backed secrets
(API keys, tokens, session identifiers) after template substitution. When a request fails
(timeout, connection error, or unexpected transport failure), the application emits ERROR-level
log lines that can include the full URL as it would appear on the wire.

Those logs feed support troubleshooting, local developer consoles, and CI-captured test logs
guarded by an ERROR allowlist. Exposing credential-bearing URL content in ERROR logs creates
unnecessary secret leakage risk in shared log bundles and undermines the sensitive-data posture
documented in PYPOST-685 and PYPOST-688.

**Business intent:** Close P1 observability debt item R-P1-001 so HTTP failure diagnostics remain
useful for operators and maintainers without leaking live credentials from resolved or
credential-bearing URLs.

## Programming Language

Python (existing PyPost desktop application codebase).

## User Stories

- As an **operator**, I want HTTP failure logs to omit secrets from URLs, so I can share log
  output or CI artifacts without exposing API keys or tokens embedded in query strings or path
  segments.
- As a **maintainer**, I want ERROR logs from HTTP client failure paths to stay within the
  project's sensitive-data-in-logs expectations, so observability work aligns with the
  PYPOST-688 audit remediation backlog.
- As a **CI operator**, I want HTTP client ERROR log shapes to remain compatible with the test
  log guardrail allowlist (or be updated deliberately), so merges are not blocked by unexpected
  ERROR noise or unlisted message patterns.
- As a **support engineer**, I still need enough context in ERROR logs (HTTP method and
  non-sensitive URL identity such as host and path) to distinguish which request failed when
  multiple tabs or retries are in flight.

## Definition of Done

The task is complete when all of the following acceptance criteria are met:

| ID | Criterion |
| --- | --- |
| AC-1 | Timeout ERROR logs contain no resolved secret values from URL query, path, or host |
| AC-2 | Connection failure ERROR logs contain no resolved secret values |
| AC-3 | Generic transport failure ERROR logs contain no resolved secret values |
| AC-4 | Request preparation failure ERROR logs (e.g. body format conversion) contain no resolved
  secret values |
| AC-5 | Each ERROR log retains HTTP method and non-sensitive URL identity for correlation |
| AC-6 | Automated tests cover at least one failure path with environment-resolved secrets in the
  URL |
| AC-7 | CI ERROR log guardrails remain valid after any message shape change |
| AC-8 | PYPOST-688 finding R-P1-001 / L-001 can be marked remediated in follow-up tech-debt
  documentation |

**Summary:** ERROR-level log lines emitted on HTTP send failure paths must not contain
environment-resolved secret values or sensitive query/path token content. Operators can still
identify which request failed from log context without reading raw credential material. All four
known ERROR failure categories (timeout, connection failure, generic transport failure, and
pre-send preparation failure) are covered consistently.

## Task Description

**Problem:** PYPOST-688 (finding L-001, cross-ref PYPOST-685 E-003) identified that HTTP client
ERROR logs can expose URLs containing live credentials — for example query parameters with API
keys after environment substitution. Example failure modes called out in the audit:

```text
Request timed out: GET https://api.example.com/v1?key=secret
Connection failed: POST https://...
```

**Why now:** R-P1-001 is prioritized P1 (high) tech debt from the observability audit. It is
tracked as [PYPOST-741](https://pypost.atlassian.net/browse/PYPOST-741) under the PYPOST-688
remediation program. Leaving it open leaves a known credential-exposure path in production and
test logs.

### Functional requirements

- Sanitize or redact URL content in all HTTP client ERROR log emissions tied to HTTP send
  failures so that resolved environment values and common credential query parameters are not
  written verbatim.
- Preserve diagnostic value: each ERROR log must still convey the HTTP method and enough URL
  identity (e.g. host and path without sensitive query material) for an operator to correlate
  the failure with a request.
- Behavior must be consistent across all four ERROR failure categories listed in Definition of
  Done.
- Changes must not weaken existing automated checks that assert secrets are absent from ERROR
  logs on connection failure.

### Non-functional requirements

- **Security:** Treat ERROR logs as potentially shareable; assume they may be copied into
  support tickets or CI artifacts.
- **Observability:** Redaction must not remove all URL context — blank or generic logs that
  prevent distinguishing endpoints are unacceptable.
- **Compatibility:** Any change to log message prefixes must be reflected in CI ERROR log
  guardrails so allowlists stay accurate.
- **Consistency:** Align with the project's broader sensitive-data handling goals (history
  masking, MCP response sanitization) without requiring identical behavior in out-of-scope
  modules.

### Constraints and assumptions

- Implementation language is Python; scope is limited to HTTP client ERROR logging on HTTP
  failure paths.
- The task remediates logging only — not user-visible error dialogs, alert webhooks, or history
  persistence (unless unavoidable side effects are discovered and tracked separately).
- Operators may save URLs with inline secrets (not only template placeholders); redaction must
  account for credential-bearing URL text regardless of whether substitution occurred.

### In scope

- ERROR-level log lines for HTTP send failures: request timeout, connection failure, generic
  transport failure, and pre-send request preparation failure.
- Automated tests asserting redacted ERROR log output for failure scenarios.
- CI ERROR log guardrail updates if message shapes change.

### Out of scope

- WARNING/DEBUG URL logging in the HTTP client (e.g. response body truncation that logs a
  resolved URL — separate follow-up if needed).
- AlertManager endpoint or webhook URL logging (PYPOST-744, PYPOST-745).
- Console output bypass in config/style managers (PYPOST-742).
- Migrating legacy log messages to structured event naming (PYPOST-751).
- DEBUG-level curl URL logging (audit L-002, P3).
- Configurable application log level (PYPOST-743).
- User-facing error messages shown in the UI (may still contain resolved URLs; not part of this
  logging remediation unless explicitly expanded later).

## Main entities and interactions

| Entity | Attributes | Role |
| --- | --- | --- |
| **HTTP request** | Method, URL template, headers, body | Operator-defined call sent through PyPost |
| **Resolved URL** | Host, path, query parameters (may contain secrets) | URL after environment/template substitution — may contain live secrets on the wire |
| **Application log entry** | Severity, message, request identifiers | ERROR-level record written on send failure |
| **Support log bundle** | Aggregated log lines from app or test runs | Collected logs used for debugging and CI guardrails |
| **Environment variable** | Name, secret or configuration value | Substituted into URL templates |

**Interaction (business flow):** Operator sends request → HTTP layer fails → application writes
ERROR log → log may be captured locally, in CI, or shared for support → log must not expose
credential material from the URL while still identifying the failed request.

## Q&A

- **Q:** Why is this P1 if some failure paths already log the URL template with placeholders
  instead of resolved values?
  **A:** Residual risk remains when operators save literal credential-bearing URLs, when partial
  substitution embeds secrets, or when audit-identified paths still log sensitive content.
  PYPOST-688 and PYPOST-685 classify credential exposure in ERROR logs as P1 regardless of
  template-vs-resolved nuance. Requirements target the business outcome: ERROR logs must not
  leak secrets.

- **Q:** Should user-visible error messages (e.g. "Request to https://… timed out") be redacted?
  **A:** Out of scope for this task. Scope is application ERROR logging only; UI error text is a
  separate product decision.

- **Q:** How does this relate to PYPOST-709?
  **A:** PYPOST-709 was an earlier ticket for PYPOST-685 E-003; PYPOST-741 is the active Jira
  debt item under PYPOST-688 R-P1-001. This task supersedes that remediation track.

- **Q:** Must redaction match history masking exactly?
  **A:** Not required to be identical in Step 1. Business goal is consistent sensitive-data
  posture; exact parity with history or MCP sanitizers is an implementation concern for Step 2.

- **Q:** Are alert webhook logs in scope?
  **A:** No. AlertManager endpoint and webhook URL verbosity are tracked as PYPOST-744 and
  PYPOST-745.

## Business risks identified during requirements gathering

1. **Audit vs observed behavior:** PYPOST-688 L-001 states fully rendered URLs may appear in
   ERROR logs, while some current failure paths may log URL templates instead. Residual risk
   remains regardless — requirements target the outcome that ERROR logs must not contain
   credential-bearing URL content.

2. **Literal URL secrets:** Operators who save URLs with inline secrets (no placeholders) would
   still leak credentials in ERROR logs unless redaction addresses this case.

3. **Adjacent non-ERROR exposure:** Response body truncation may log resolved URLs at WARNING
   severity. Out of scope for this ticket but noted for potential follow-up.

4. **User-facing error messages:** Raised exceptions may include resolved URLs in messages
   shown in the UI. Out of scope for logging remediation; track separately if product wants UI
   parity.

5. **CI guardrail coupling:** HTTP client ERROR message prefixes are allowlisted for CI log
   guardrails. Message shape changes require deliberate guardrail updates to avoid blocking
   merges.
