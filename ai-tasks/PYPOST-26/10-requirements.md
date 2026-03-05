# Requirements: PYPOST-26 - Chunked Response Streaming

## Goals
Ensure correct handling of HTTP responses with `Transfer-Encoding: chunked`. Currently, the application might hang or not display the response until it is fully downloaded, which is problematic for large responses or streams.

## User Stories
- As a user, I want the application to handle chunked responses correctly and display the result.
- As a user, I want to see the response content even if it is transmitted in chunks.

## Acceptance Criteria
- [ ] **Chunked Encoding**: The client correctly processes responses with `Transfer-Encoding: chunked`.
- [ ] **Streaming**: The response is read in chunks (stream) to avoid loading the entire file into memory at once (although for display in `ResponseView` we still accumulate it, but the reading process should be robust).
- [ ] **No Freezes**: The application does not freeze when receiving chunked data.

## Task Description
Update `HTTPClient` to use `stream=True` in `requests` and read data in chunks.

### Technical Details
- **Component**: `HTTPClient`.
- **Library**: `requests`.
- **Method**: `iter_content` or `iter_lines`.
