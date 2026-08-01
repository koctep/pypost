# PYPOST-950: Align timeout-diagnostics with text-wait settle

## Goals

PYPOST-920 moved golden Send settle to identity-scoped `wait_for_text` on
response status and body. The forced-timeout companion test still used a
snapshot predicate miss, so maintainers could not rely on one settle path for
both happy and failure diagnostics. This task closes TD-3 from PYPOST-920 by
aligning the timeout lock with the text-wait pattern while preserving the
existing `step` and `response_excerpt` contract.

## User Stories

- As a **maintainer**, I want the golden timeout-diagnostics test to exercise
  the same text-wait settle path as the happy-path golden test, so failure
  fingerprints stay consistent when triaging Send settle timeouts.
- As a **contributor**, I want forced-timeout diagnostics to still include
  `step=wait_response_after_send` and a panel excerpt, so CI output remains
  actionable without reading snapshot trees.

## Definition of Done

- Golden forced-timeout test forces a short `wait_for_text` miss (not
  `wait_for_snapshot`).
- Wrapped `UiWaitTimeoutError` still carries `diagnostics["step"]` and
  `diagnostics["response_excerpt"]`.
- Inner text-wait diagnostics (`widget_id`, `expected`) are preserved through
  the wrap.
- Scoped golden / agent e2e tests pass.
- Developer docs note text-wait timeout diagnostics for golden.

## Task Description

**Problem:** `test_agent_golden_settle_timeout_includes_step_and_excerpt`
forces `session.wait_for_snapshot(lambda _snap: False, …)` while golden happy
path and sibling settle helpers use `wait_for_text` on `RESPONSE_STATUS` /
`RESPONSE_BODY`. The asymmetry was intentional in PYPOST-920 but listed as
follow-up TD-3.

**Parent:** PYPOST-920 (response status/body identity + golden text-wait
settle).

**Constraints:**

- Test-harness only — no production code changes required.
- Do not change happy-path golden settle or shared send-settle helper behavior.
- Preserve existing timeout markers and agent e2e markers.

**Out of scope:**

- Migrating sibling e2e modules (PYPOST-948).
- Tab-scoped session text waits (PYPOST-949).
- New wait primitives or production logging.

## Q&A

- Q: Why not use `wait_response_after_send` directly?
  A: Golden test inlines the wrap pattern to lock the golden-specific step
  name and excerpt shape; alignment means matching `wait_for_text`, not
  necessarily importing the helper.
- Q: How to force a text-wait miss reliably?
  A: Wait for an impossible status label (e.g. `Status: 999`) with a short
  budget after Send — response may arrive as 200 but text never matches.
