# PYPOST-1213: Observability

## Existing Evidence

No runtime instrumentation is added by this documentation-only diagnosis. The
PYPOST-1212 harness already captures bounded stdout/stderr tails, faulthandler output,
signal and exit-code classification, environment metadata, batch topology, and duration.

## Diagnostic Signals Used

- `SIGSEGV` / exit code 139 identifies the native crash.
- `StyleManager.apply_theme` and `QStyleFactory.create` identify the crash surface.
- Clean exit code 0 in bounded and isolated processes provides the contrast.

## Validation

The existing structured evidence is sufficient for the diagnosis and for the
PYPOST-1214 mitigation handoff. No Prometheus or application metrics are applicable to
this test-harness diagnosis.
