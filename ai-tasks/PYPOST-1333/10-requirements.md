# PYPOST-1333: Sanitize rendered URLs in sse_stream_detected and retry log events

## Goals

Operators and support staff must be able to diagnose SSE detection and HTTP retry
failures from application logs and exhaustion alerts without risking query-string
secrets (or other environment-resolved secret values embedded in URLs) leaking into
those sinks. Users who trigger a request should still understand that a timeout or
connection failure occurred for the intended host.

This closes the remaining generic log/alert gap identified after PYPOST-1316
(TD-1) and complements PYPOST-1122, which already covered
`response_body_truncated`.

## User Stories

- As an operator reviewing DEBUG/WARNING logs, I want rendered request URLs in
  `sse_stream_detected`, `retryable_error`, and `retry_exhausted` to redact secret
  query values the same way ERROR transport logs already do, so shared log
  aggregators do not retain credentials.
- As an on-call engineer receiving retry-exhaustion alerts, I want the alert’s
  final error message to be free of rendered URL secrets, so webhook and alert-file
  sinks are safe to retain.
- As a collection author using query-string API tokens, I want failed retry paths
  not to write those tokens into logs when a timeout or connection error embeds the
  rendered URL in the error text.

## Definition of Done

- `sse_stream_detected` log lines do not contain unsanitized rendered URL secrets.
- `retryable_error` and `retry_exhausted` log lines do not embed unsanitized rendered
  URL secrets via the error message text.
- Exhaustion alert `final_error_message` does not embed unsanitized rendered URL
  secrets for timeout/connection failures.
- Automated tests prove the redaction for these paths (caplog / assertLogs).
- PYPOST-1122 (`response_body_truncated`) behavior remains intact; this task does
  not re-implement that work.
- Path-segment rejection work (PYPOST-1346 / PYPOST-1332) is out of scope and
  unchanged.

## Task Description

Today, transport ERROR logs sanitize resolved URLs before writing them. Two sibling
observability paths still do not:

1. When an SSE stream is detected, the DEBUG event logs the full rendered URL.
2. When retries warn or exhaust, they log the execution error message. For timeouts
   and connection failures that message embeds the full rendered URL, so secrets in
   the query string can appear in WARNING logs and in alert payloads.

Programming language: **Python**.

## Q&A

- **Q:** Why is this needed if GitLab tokens are only in `Authorization`?
  **A:** Other collections may place secrets in query parameters. The gap is
  generic, not GitLab-specific.
- **Q:** Does this re-do PYPOST-1122?
  **A:** No. That ticket already redacts `response_body_truncated`. This ticket
  covers the remaining events called out in PYPOST-1316 TD-1 and the exhaustion
  alert note from PYPOST-1334.
- **Q:** Must the on-screen UI error keep the raw URL?
  **A:** Prefer not leaking secrets into any durable sink. A log-safe URL in the
  user-visible timeout/connection message is acceptable; the user already knows
  their own secrets.
