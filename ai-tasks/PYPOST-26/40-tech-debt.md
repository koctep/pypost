# PYPOST-26: Technical Debt Analysis


## Shortcuts Taken

- **Global Timeout Hardcoding**: We introduced a hardcoded timeout of `30.0` seconds in `HTTPClient.send_request`. Ideally, this should be configurable by the user per request or in global settings. — [PYPOST-194](https://pypost.atlassian.net/browse/PYPOST-194)
- **Metrics Estimation**: While streaming, we estimate the size based on the utf-8 encoded length of the text received so far. This is generally accurate for text but might differ slightly from wire bytes. — [PYPOST-195](https://pypost.atlassian.net/browse/PYPOST-195)
- **Time Updates**: The Status code is updated immediately via `headers_received` signal, but "Elapsed Time" is only final when the request completes. We don't update "Elapsed Time" in real-time during streaming (it stays "-" until finished). — [PYPOST-196](https://pypost.atlassian.net/browse/PYPOST-196)

## Code Quality Issues

- **HTTPClient.send_request Complexity**: [FIXED in PYPOST-8] The method is getting slightly large with the try-except blocks, fallback logic for JSON, and streaming loop. It could be refactored into smaller helper methods.

## Missing Tests

- **SSE Endpoint Automated Test**: We verified manually with `test_streaming.py`, but haven't integrated a permanent test suite for SSE. — [PYPOST-197](https://pypost.atlassian.net/browse/PYPOST-197)
- **Cancellation Test**: We haven't added an automated test to verify that clicking "Stop" actually terminates the connection immediately. We observed that checking the flag only once per chunk might be delayed if chunks are large or slow; we improved this by checking again after processing, but `requests` loop is still the driver. — [PYPOST-198](https://pypost.atlassian.net/browse/PYPOST-198)

## Performance Concerns

- **Memory Usage on Large Streams**: We still accumulate the full body in `content_parts` (in `HTTPClient`) and `body_view` (in UI). An infinite stream will eventually consume all memory. For production SSE support, we should probably only keep a buffer of the last N lines or allow clearing the view. — [PYPOST-199](https://pypost.atlassian.net/browse/PYPOST-199)

## Follow-up Tasks

- Add "Timeout" configuration to `RequestData` model and UI. — [PYPOST-200](https://pypost.atlassian.net/browse/PYPOST-200)
- Implement "tail" mode for logging/streaming (limit buffer size). — [PYPOST-201](https://pypost.atlassian.net/browse/PYPOST-201)
- Add real-time "Elapsed Time" counter in UI during request. — [PYPOST-202](https://pypost.atlassian.net/browse/PYPOST-202)
- Refactor `HTTPClient` to better handle different content types and errors. — [PYPOST-203](https://pypost.atlassian.net/browse/PYPOST-203)


