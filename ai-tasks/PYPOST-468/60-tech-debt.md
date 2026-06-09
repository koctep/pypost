# PYPOST-468: Technical Debt Analysis

## Shortcuts Taken

- Used `urllib.parse.parse_qsl(parsed_url.query)` without `keep_blank_values=True`. This may inadvertently strip empty query parameters from the original URL (e.g., `?foo=&bar=baz` becomes `?bar=baz`).

## Code Quality Issues

- The query parameter merging logic in `CurlGenerator` loops over `request.params.items()` which is a `dict`. This inherently limits support for duplicate query keys (e.g., `?id=1&id=2`) which is a broader issue in how parameters are stored.
- Clipboard error handling in `TabsPresenter._handle_copy_curl_request` catches a generic `Exception`. It should ideally catch specific UI or clipboard exceptions.
- `CurlGenerator.generate` is a single long method. If more cURL options are added in the future, it should be broken down into smaller helper methods (`_build_url`, `_build_headers`, etc.).

## Missing Tests

- No test cases verifying behavior with empty query parameters or duplicate keys.
- No test cases for URLs containing URL fragments (`#hash`).
- No tests simulating clipboard failures in the UI layer.

## Performance Concerns

- None currently identified. Generating the cURL string is very lightweight.

## Follow-up Tasks

- [ ] Fix query string parsing to preserve empty values (`keep_blank_values=True`).
- [ ] Add tests for query string edge cases (empty values, URL fragments).
- [ ] Refactor `request.params` handling across the app to support duplicate keys, and update `CurlGenerator` to match.
