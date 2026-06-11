# PYPOST-197: Close debt — permanent SSE automated test suite

## Goals

Close follow-up debt from [PYPOST-26](https://pypost.atlassian.net/browse/PYPOST-26): replace
manual SSE verification with a permanent pytest module.

## Definition of Done

- [x] `tests/test_http_client_sse_probe.py` in CI test suite
- [x] Covers SSE auto-detection, read timeout, and non-200 responses
- [x] Aligned with [PYPOST-39](https://pypost.atlassian.net/browse/PYPOST-39) MCP probe tooling

## Task Description

Sprint 492 debt closure. Replaces ad-hoc `test_streaming.py` manual checks.
