# PYPOST-1250: Requirements

## Goal

Expand regression coverage for strict template expressions at the boundaries identified in
PYPOST-1120 technical debt.

## Scope

- Three or more nested allow-listed calls, including strict `to_int` conversion.
- Newline-formatted strict expressions.
- Jinja comments containing strict expressions.

Production code and conversion semantics are out of scope.

## Acceptance Criteria

- The focused test module covers successful deep nesting and strict failure propagation.
- Multiline strict syntax behavior is explicitly recorded by a regression test.
- Commented expressions verify that Jinja does not evaluate valid commented content while
  strict validation remains fail-closed for malformed strict expressions.
- Every test has an explicit timeout marker.
