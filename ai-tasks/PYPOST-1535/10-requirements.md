# PYPOST-1535: MCP server impl RequestData identity failures

## Goals

Restore confidence in the MCP server tool-registration contract so automated
quality gates stop failing on false identity mismatches. Operators and
developers must be able to trust that registering a request as an MCP tool
keeps a stable handle to that same request for subsequent tool calls, without
surprising object replacement that breaks verification and debugging.

## User Stories

- As a PyPost developer, I want MCP server unit tests that encode the
  registration contract to pass, so the suite reflects real product behavior
  rather than a copy-induced identity break.
- As a maintainer of MCP tool refresh, I want tool registration to remain safe
  under concurrent list/call traffic, so live collection refresh does not
  expose a partially cleared tool catalog.
- As a sprint gate owner, I want this pre-existing debt cleared so unrelated
  tasks are not blocked by `tests/test_mcp_server_impl.py` identity failures.

## Definition of Done

- The four identity-sensitive cases in `tests/test_mcp_server_impl.py` pass:
  register keeps the exposed request object; `call_tool` passes that same
  object into request execution (including default-arg and explicit-arg paths).
- Concurrent-safe atomic replacement of the tool map remains in place (no
  return to in-place `clear()` mid-flight).
- Focused `make test` for those cases is green.
- No new skip/xfail markers hide the failures.

## Task Description

Pre-existing failures show `assertIs` comparing two `RequestData` values that
are equal field-for-field (including the same `id`) but are not the same Python
object. That breaks the expectation that registering a request stores and later
executes that request instance. The business need is a correct, trustworthy
registration contract: either the product must preserve identity where the
suite (and callers) rely on it, or tests must be rewritten only if product
isolation correctly requires distinct copies — decided by which behavior
matches the intended MCP tool lifecycle.

Programming language: **Python**.

## Q&A

- **Q**: Why not only weaken tests to `assertEqual`?
  **A**: Identity checks document that execution uses the registered tool
  object. Weakening them is only correct if the product intentionally stores
  copies as the contract; investigation showed atomic map swap is the required
  concurrency property, while deep-copying at register is redundant with
  upstream isolation and caused this debt.
- **Q**: Is this a new feature?
  **A**: No — Debt / failing-test recovery for a regression introduced when
  atomic `register_tools` was added.
