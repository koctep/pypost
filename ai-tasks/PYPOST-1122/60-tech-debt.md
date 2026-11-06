# PYPOST-1122: Technical Debt Analysis

## Shortcuts Taken

- Reused `_error_log_url` for WARNING without renaming the helper. Name still says "error" while
  the function is now the shared log-safe URL helper for ERROR and WARNING.

## Code Quality Issues

- Helper name `_error_log_url` is slightly misleading after WARNING reuse. Cosmetic; rename only
  if a broader logging-URL audit lands.

## Missing Tests

- No dedicated assertion for literal (non-placeholder) query secrets on the truncation path.
  ERROR logging already covers that heuristic via `sanitize_text`; truncation reuses the same
  helper. Optional parity test if desired later.

## Performance Concerns

None — one `sanitize_text` call only when truncation already occurred.

## Follow-up Tasks

| Item | Priority | Notes |
| --- | --- | --- |
| Rename `_error_log_url` → shared log-safe URL helper | Low | Optional clarity; not required for correctness |
| Adjacent URL logs (`sse_stream_detected`, retry WARNING events) | Low | Already tracked: [PYPOST-1333](https://pypost.atlassian.net/browse/PYPOST-1333) |
| `ExecutionError` UI messages still contain resolved URLs | Low | Product decision (from PYPOST-741 debt) |
| Path-segment secrets without query heuristics | Low | Needs `hidden_keys` in HTTPClient if required |
| `make lint-tests` E501 in `tests/test_mcp_server_registry.py:308` | Low | Pre-existing; unrelated to this change (reproduced with our diff stashed) |

No blockers. Safe to close after reviews and commit.
