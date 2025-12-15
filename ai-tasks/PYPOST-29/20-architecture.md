# Architecture: PYPOST-29 - Chunked Response Streaming

## Research
The `requests` library supports streaming responses via `stream=True`.
To read the body, `response.iter_content(chunk_size=...)` should be used.

## Implementation Plan

1.  **Update `HTTPClient.send_request`**:
    -   Set `stream=True` in `requests.request`.
    -   Read body:
        ```python
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
        ```
    -   Save `content` to `ResponseData`.

## Architecture

### `HTTPClient`

Modified `send_request` method to handle streaming.
Accumulates chunks into a single byte string for display.
*Note*: For very large files, we might need to avoid loading everything into memory, but for now (text/JSON responses) accumulation is acceptable.
