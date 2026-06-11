# PYPOST-74: NullMetrics no-op to remove metrics guards

## Goals

After PYPOST-73 introduced `MetricsTrackerProtocol`, every tracking call site still wraps
metrics in `if self._metrics:` guards. That boilerplate obscures business logic and duplicates
the optional-injection pattern across services, MCP, and UI layers.

Introduce a shared no-op implementation so consumers always hold a tracker and call through
without null checks.

## User Stories

- As a **developer**, I want to call `self._metrics.track_*()` directly so observability
  wiring does not clutter control flow.
- As a **test author**, I want omitted metrics to default to a safe no-op instead of `None`.
- As a **maintainer**, I want one place (`resolve_metrics`) to normalize optional injection.

## Definition of Done

- [x] `NullMetrics` implements all `MetricsTrackerProtocol` methods as no-ops.
- [x] `resolve_metrics(None)` returns shared `NULL_METRICS` singleton.
- [x] Consumer constructors use `resolve_metrics`; no `if self._metrics:` guards remain.
- [x] Conditional tracking (e.g. hidden-key count, cancelled errors) keeps business guards only.
- [x] Tests pass; NullMetrics covered in `tests/test_metrics_protocol.py`.

## Task Description

Source: PYPOST-44 technical-debt item TD-2. Overlaps with [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) scope — implemented here.

**In scope:** NullMetrics, resolve helper, guard removal, tests, dev docs.

**Out of scope:** Changing Prometheus metric names; MetricsManager facade split (PYPOST-75 counters).

## Q&A

| Question | Answer |
| --- | --- |
| Why not default param `NULL_METRICS` everywhere? | `resolve_metrics` keeps explicit `None` call sites working without mutable-default pitfalls. |
| Does behavior change when metrics omitted? | No — tracking was already skipped; NullMetrics preserves that silently. |
