# PYPOST-1257 Code Cleanup

- Moved the existing protocol method discovery and signature-parity logic into
  `tests/helpers/protocol_guards.py` without changing its diagnostics or
  checks.
- Kept metrics-specific dummy argument generation in
  `tests/test_metrics_protocol.py` because it depends on metrics domain types.
- Added a focused generic protocol test with the repository-required timeout
  marker.
- The delegated review worker was unavailable; the orchestrator performed the
  focused local review and Make-driven checks.
