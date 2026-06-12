# PYPOST-119: Observability

## Existing metrics

`VariableHoverResolver` already exports template render metrics via `render_path="hover"` when
metrics are configured (`VariableHoverResolver.set_metrics`). No new counters added.

## Performance impact

- Reduced `find_expression_at_index` and `resolve_text` calls on repeated moves at the same
  scan index — observable as lower CPU during pointer jitter over one token.
- No user-visible logging changes.

## Deferred

- Per-widget hover cache hit/miss metrics — out of scope; add only if profiling shows need.
