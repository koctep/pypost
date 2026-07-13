# PYPOST-753: Cap HTTP response body size

## Goals

Prevent OOM from unbounded `iter_content` buffering on large HTTP downloads.

## Definition of Done

- [x] `max_response_bytes` on `AppSettings` (default 50 MiB)
- [x] HTTPClient stops reading when cap exceeded
- [x] Partial body returned with truncation notice
- [x] `response_body_truncated_total` metric
- [x] Unit tests with mocked oversized stream
