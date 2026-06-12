# PYPOST-80: Architecture

## Current State

`pypost/core/http_client.py` implements HTTP transport (`HTTPClient.send_request`, SSE probe,
template rendering, metrics). Style debt TD-1 flagged trailing whitespace on several lines.

## Change Plan

1. Scan `pypost/core/http_client.py` line-by-line for trailing spaces or tabs.
2. Remove any violations (none found at execution time).
3. Run `tests/test_http_client.py` and `tests/test_http_client_sse_probe.py` to confirm no
   regression.

## Data Flow

Unchanged — whitespace cleanup does not alter request/response handling.

## Out of Scope

- Other modules or flake8 debt elsewhere in `pypost/`.
- Adding new lint CI gates (separate backlog items).
