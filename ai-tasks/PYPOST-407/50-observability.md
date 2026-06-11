# PYPOST-407: Observability

## Analysis

This task is a structural refactor: centralizing copy semantics and documenting policy. No new
user-facing operations or failure modes are introduced. Existing INFO logs on collection open
and tab restore remain unchanged.

## Logging

No new log lines added. Copy operations are not hot enough to warrant per-copy DEBUG metrics
without profiling evidence.

## Metrics

No new metrics. Tab-open counters (`track_gui_new_tab_action` on context menu) are unchanged.

## Deferred Observability

Optional follow-up if large-body requests become common:

- DEBUG log of approximate copy payload size at `add_new_tab` (body + headers byte counts).
- Histogram of copy duration if profiling shows tab-open latency issues.

Neither is required to close PYPOST-407.
