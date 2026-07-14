# PYPOST-746 — Requirements

> Parent: [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) audit R-P2-004

## Problem

`MetricsRegistry._init_metrics` is a 196-LOC method that registers all 31 Prometheus
instruments in one block, making the registry harder to navigate and extend.

## Acceptance Criteria

1. Extract four private helpers on `MetricsRegistry`:
   - `_init_gui_metrics`
   - `_init_http_metrics`
   - `_init_mcp_metrics`
   - `_init_encryption_metrics`
2. `_init_metrics` delegates to the four helpers in the same order as today.
3. No change to metric names, labels, help strings, or public `track_*` API.
4. Existing metrics tests pass (`make check`).
5. Developer docs reflect the domain split.

## Out of Scope

- New metrics or label changes
- Splitting `track_*` methods
- OTel adapter changes
