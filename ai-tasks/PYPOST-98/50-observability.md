# PYPOST-98: Observability

## Assessment

No new logging or metrics. JSON validation errors are already surfaced in the body editor
via `ValidationController` (error banner and line markers). The highlighter remains
silent by design.

## Rationale

Validation failures are user-facing editor state, not operational telemetry. Existing
body editor validation docs cover troubleshooting invalid JSON.
