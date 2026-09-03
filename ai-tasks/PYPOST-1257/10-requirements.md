# PYPOST-1257 Requirements

## Business reason

Protocol conformance checks were implemented inside the metrics test module.
Keeping the reflection-based guard there makes it difficult to reuse when
additional `runtime_checkable` protocols need structural contract tests.

## Functional requirements

1. Extract `_assert_tracker_satisfies_all_protocol_methods` into
   `tests/helpers/protocol_guards.py`.
2. Move the protocol-method discovery it depends on with the guard.
3. Update metrics protocol tests to import and use the shared helper without
   changing the existing conformance behavior.
4. Prove the helper works with a runtime-checkable protocol independent of the
   metrics protocol.

## Non-functional requirements

- Preserve method presence, callability, parameter count, parameter name,
  parameter kind, and default-value checks.
- Keep the helper test-only; no production code or runtime dependency changes.
- Keep repository operations and validation Make-driven.

## Out of scope

- Changing metrics protocol definitions or tracker implementations.
- Changing the dummy-value invocation logic used only by the metrics tests.
- Introducing protocol negotiation or a new production abstraction.

## Acceptance criteria

- `tests/helpers/protocol_guards.py` provides the extracted guard.
- `tests/test_metrics_protocol.py` no longer defines a duplicate guard.
- Shared-helper and metrics conformance tests pass.
- Lint, type checking, and AI-task artifact verification pass.
