# PYPOST-1534: Observability

## Analysis

This task corrects an over-broad blank-segment guard so empty-path URLs no longer fail
closed. Existing ERROR events from PYPOST-1332 / PYPOST-1346 remain the operational
signals for real rejects:

| Event | Logger | When |
| ----- | ------ | ---- |
| `blank_path_segment_rejected` | `pypost.core.http_client` | Mid-path `//` or trailing blank |
| `dot_path_segment_rejected` | `pypost.core.http_client` | Whole-segment `.` / `..` |

Empty-path prepares/sends do **not** emit either event (correct — nothing was rejected).

## Changes

- **No new log events or metrics.**
- **No allowlist changes** — existing `tests/expected_log_allowlist.yaml` entries for
  `blank_path_segment_rejected` / `dot_path_segment_rejected` stay valid for intentional
  reject tests.
- Side effect: false-positive `blank_path_segment_rejected` lines for origin-only URLs
  (e.g. fixture `http://x`) no longer appear during ordinary HTTP client tests.

## Validation

- Blank-segment rejection tests still assert `blank_path_segment_rejected` with
  origin-bounded URL.
- Empty-path control test asserts prepare succeeds without requiring ERROR logs.
- Checklist: existing ERR-level reject logging retained; no large URL bodies logged;
  origin-only URL helper unchanged.

## N/A Notes

New observability instrumentation is N/A for this debt fix; behavior change is narrowing
when the existing reject path fires, not adding a new signal.
