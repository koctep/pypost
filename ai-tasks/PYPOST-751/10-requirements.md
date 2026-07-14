# PYPOST-751: Standardize http_client log messages

## Goals

Close PYPOST-688 finding R-P3-003 by migrating three legacy human-readable ERROR log prefixes
in `HTTPClient.send_request` to structured key=value events consistent with the project logging
convention ([PYPOST-747](https://pypost.atlassian.net/browse/PYPOST-747)).

## Definition of Done

| ID | Criterion |
| --- | --- |
| AC-1 | Timeout path logs `http_request_timed_out method=… url=…` |
| AC-2 | Connection path logs `http_connection_failed method=… url=…` |
| AC-3 | Generic transport path logs `http_request_failed method=… url=… detail=…` |
| AC-4 | URLs remain sanitized via `_error_log_url` ([PYPOST-741](https://pypost.atlassian.net/browse/PYPOST-741)) |
| AC-5 | `tests/expected_log_allowlist.yaml` lists new event prefixes |
| AC-6 | `TestHTTPClientErrorLogging` asserts event names and redaction |
| AC-7 | `make check` passes |

## Out of scope

- DEBUG/WARNING log migration in `http_client.py`
- UI error dialog strings (`Request failed:` in collection dialogs)
