# PYPOST-1257 Architecture

## Shared test boundary

```text
runtime_checkable Protocol
          │
          ▼
tests.helpers.protocol_guards
  ├─ _get_protocol_methods
  └─ _assert_tracker_satisfies_all_protocol_methods
          │
          ├─ metrics protocol tests
          └─ future protocol contract tests
```

`protocol_guards.py` owns only reflection and signature-parity verification.
It accepts the protocol explicitly when callers need a protocol other than
the existing metrics contract. The metrics test module retains its
metrics-specific dummy argument generation and imports the shared guard.

The extraction is behavior-preserving: missing public methods remain failures,
non-callable attributes remain failures, and parameter count, name, kind, and
default mismatches retain the existing diagnostics.
