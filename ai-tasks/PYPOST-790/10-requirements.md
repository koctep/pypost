# PYPOST-790: Per-test duration in pytest output

## Goals

Developers should see how long each test took without scrolling to the `--durations` block.

## Definition of Done

- [x] Verbose lines show call duration (`PASSED [1.23s]`)
- [x] Top 5 slowest tests printed after session (call duration)
- [x] CI `--durations` audit unchanged
- [x] Documented in `doc/dev/testing.md`

## Technical choice

Duration metric: **call phase only** (`report.when == "call"`), matching pytest `--durations`
semantics used by `audit_test_durations.py`.
