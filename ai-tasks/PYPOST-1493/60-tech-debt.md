# PYPOST-1493: Technical Debt Analysis

## Shortcuts Taken

- Post-response repro still uses a short child-side `time.sleep(0.05)` only to
  force deterministic ordering (response before stderr). Production wait path
  uses condition notify, not sleeps.
- Call sites that still use bare `get_stderr()` after `wait_for_response` can
  flake if they assert presence; they must migrate to `wait_for_stderr`.

## Code Quality Issues

- Stderr notify wakes all condition waiters (including response waiters); this
  is harmless but slightly chatty under heavy stderr. A dedicated stderr
  condition could isolate wake-ups if needed later.
- `wait_for_predicate` interval fallback remains useful for non-stream
  predicates; stderr-specific waits should prefer `wait_for_stderr`.

## Missing Tests

- No multi-worker stress that loops the post-response stderr wait hundreds of
  times (relies on suite parallelism + deterministic delayed-stderr repro).
- No explicit unit test that `wait_for_stderr` raises `TimeoutError` on a
  missing substring (optional follow-up).

## Performance Concerns

- Negligible: one `notify_all` per stderr line under the existing condition
  lock; typical MCP child diagnostics are low volume.

## Follow-up Tasks

| Item | Class | Notes |
| --- | --- | --- |
| Audit other suites for bare `get_stderr()` after `wait_for_response` | Follow-up debt | Migrate presence asserts to `wait_for_stderr` |
| Optional timeout-path unit test for `wait_for_stderr` | Follow-up debt | Assert `TimeoutError` message includes stderr snapshot |
| Dedicated stderr condition (vs shared notify) | Follow-up debt | Only if shared wake-ups become measurable noise |
