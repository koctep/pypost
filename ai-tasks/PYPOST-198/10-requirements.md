# PYPOST-198: Close debt — stop-flag streaming cancellation test

## Goals

Close follow-up debt from [PYPOST-26](https://pypost.atlassian.net/browse/PYPOST-26): automated
verification that Stop terminates streaming and returns partial body.

## Definition of Done

- [x] `test_stop_flag_stops_streaming_and_returns_partial_body` in `tests/test_http_client.py`
- [x] Asserts connection stops and partial content is preserved

## Task Description

Sprint 492 debt closure. Documents acceptable chunk-boundary stop latency from `requests` driver.
