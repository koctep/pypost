# PYPOST-1122: Redact resolved URLs in http_client response_body_truncated WARNING logs

## Goals

PyPost operators send HTTP requests whose URLs may contain environment-backed secrets after
template substitution. When a response body exceeds the configured size cap, the application
emits a WARNING-level `response_body_truncated` log that includes the request URL.

ERROR-level HTTP failure logs already redact credential-bearing URL content
([PYPOST-741](https://pypost.atlassian.net/browse/PYPOST-741)). WARNING truncation logs still
expose the resolved URL, creating an inconsistent sensitive-data posture for shareable log
bundles and CI artifacts.

**Business intent:** Close the Low follow-up from PYPOST-741 so truncation diagnostics remain
useful without leaking live credentials from resolved URLs, consistent with ERROR log redaction.

## Programming Language

Python (existing PyPost desktop application codebase).

## User Stories

- As an **operator**, I want truncation WARNING logs to omit secrets from URLs, so I can share
  log output or CI artifacts without exposing API keys or tokens embedded in query strings.
- As a **maintainer**, I want WARNING truncation logs to match the sensitive-data expectations
  already applied to HTTP ERROR logs, so observability debt does not leave a residual leak path.
- As a **support engineer**, I still need enough URL identity (host and path without sensitive
  query material) in the truncation WARNING to correlate which request was truncated.

## Definition of Done

| ID | Criterion |
| --- | --- |
| AC-1 | `response_body_truncated` WARNING logs contain no resolved secret values from URL query or equivalent credential-bearing URL text |
| AC-2 | The WARNING retains HTTP method, non-sensitive URL identity, and `max_bytes` for correlation |
| AC-3 | Automated tests cover truncation WARNING logging with environment-resolved secrets in the URL |
| AC-4 | Behavior is consistent with the URL redaction applied to HTTP ERROR logs in PYPOST-741 |

**Summary:** WARNING-level `response_body_truncated` log lines must not contain
environment-resolved secret values or sensitive query/token content, while still identifying
which request was truncated.

## Task Description

**Problem:** PYPOST-741 remediated credential exposure in HTTP client ERROR logs but explicitly
left WARNING `response_body_truncated` logging out of scope. That path still logs the resolved
URL. Source: `ai-tasks/PYPOST-741/60-tech-debt.md` (follow-up ticket PYPOST-1122).

**Why now:** Residual Low-priority debt under the MCP Runtime & Request Safety sprint. Leaving
it open keeps a known credential-exposure path in WARNING logs that operators and CI may still
capture and share.

### Functional requirements

- Sanitize or redact URL content in `response_body_truncated` WARNING emissions so resolved
  environment values and common credential query parameters are not written verbatim.
- Preserve diagnostic value: method, enough URL identity for correlation, and the truncation
  limit (`max_bytes`).
- Align outcome with PYPOST-741 ERROR log redaction (same business posture).

### Non-functional requirements

- **Security:** Treat WARNING logs as potentially shareable (local console, CI, support tickets).
- **Observability:** Redaction must not remove all URL context.
- **Consistency:** Match the project's sensitive-data-in-logs expectations already applied to
  HTTP ERROR paths.

### Constraints and assumptions

- Implementation language is Python; scope is limited to the HTTP client truncation WARNING log.
- Logging remediation only — not user-visible UI messages, history persistence, or other WARNING
  / DEBUG URL log sites unless already in scope.
- Operators may save URLs with inline secrets (not only template placeholders).

### In scope

- WARNING-level `response_body_truncated` log URL field in the HTTP client.
- Automated tests asserting redacted WARNING log output on truncation.

### Out of scope

- Other non-ERROR URL logs (`sse_stream_detected`, retry WARNING events) — tracked separately
  (e.g. PYPOST-1333).
- User-facing `ExecutionError` messages that may still contain resolved URLs.
- Path-segment secrets without query heuristics / `hidden_keys` threading into HTTPClient.
- Changing truncation metrics or the truncation size policy itself.

## Main entities and interactions

| Entity | Attributes | Role |
| --- | --- | --- |
| **HTTP request** | Method, URL template | Operator-defined call |
| **Resolved URL** | Host, path, query (may contain secrets) | URL after environment/template substitution |
| **Truncation WARNING** | Severity, method, URL, max_bytes | Log written when response body exceeds cap |
| **Support log bundle** | Aggregated log lines | Shared debugging / CI artifacts |

**Interaction:** Operator sends request → response body exceeds cap → application writes
truncation WARNING → log must not expose credential material from the URL while still
identifying the truncated request.

## Q&A

- **Q:** Why a separate ticket from PYPOST-741?
  **A:** PYPOST-741 scoped ERROR failure paths only. Truncation WARNING was recorded as Low
  follow-up debt and ticketed as PYPOST-1122.

- **Q:** Must redaction be identical to ERROR logs?
  **A:** Business outcome must be consistent (no secret leakage). Exact helper reuse is an
  architecture concern for Step 2.

- **Q:** Are other WARNING/DEBUG URL logs in scope?
  **A:** No. Only `response_body_truncated`. Adjacent sites remain on their own tickets.
