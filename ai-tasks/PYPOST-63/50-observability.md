# PYPOST-63: Observability

## Summary

No observability changes. This refactor **reduces** `template_expression_render_attempts_total`
volume on the history path when no hidden keys are present (fewer `render_string` calls).

## Existing signals (unchanged)

- `template_expression_render_attempts_total{render_path,outcome}` — still emitted per actual
  `render_string` call in transport and masking paths.
- History DEBUG/INFO logs in `RequestService` unchanged.

## Verification

No new metrics required. Render reduction is an internal efficiency gain.
