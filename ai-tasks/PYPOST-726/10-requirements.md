# PYPOST-726: Clean up spurious server shutdown warnings

## Goals

Eliminate the spurious error-level warnings logged when the MCP server, the
metrics server, or the test harness's live MCP test server shut down their
background processes. These warnings were flagged in code audit finding
R-P3-003 (tracked upstream as PYPOST-686). Left unaddressed, they pollute
test output and application/server logs, masking real warnings/errors and
eroding confidence in the health of server shutdown for both developers
running the test suite and operators watching production logs.

## User Stories

- As a developer running the test suite locally or in CI, I want the MCP and
  metrics server tests to complete without spurious teardown warnings, so
  that I can trust the test output and quickly spot genuine failures
  instead of triaging noise.
- As a developer/operator running the PyPost application, I want the
  embedded MCP and metrics servers to shut down cleanly (e.g. on app close or
  server stop), so that application logs do not show alarming warnings for
  a normal, successful shutdown.
- As a maintainer of the integration test harness's live MCP test server, I
  want it to shut down the same clean way the real servers do, so behavior
  in tests matches behavior in production and the fix doesn't regress.

## Definition of Done

- No spurious error-level "pending task" teardown warnings are emitted to
  logs/output when:
  - The application's embedded MCP server stops/shuts down, in both normal
    and error/failure-to-start paths.
  - The application's embedded metrics server stops/shuts down, in both
    normal and error/failure-to-start paths.
  - The test harness's live MCP test server stops after a test using it
    completes.
- Any in-flight shutdown work still outstanding when a server is told to
  stop is given the opportunity to finish or be cancelled cleanly before
  that server is considered fully stopped, for any transport mode the
  servers support.
- The fix does not change observable server behavior, the public API of the
  MCP/metrics server components, or the meaning of existing log messages —
  only shutdown/teardown is affected.
- The full automated test suite (including MCP server, metrics server, and
  any test relying on the live MCP test server) passes with no new
  failures, flakiness, or warnings introduced.
- The remediation is verifiable: running the relevant tests (or exercising
  server start/stop manually) shows clean shutdown with no teardown warnings
  in captured output/logs.

## Task Description

### Problem

Audit finding R-P3-003 observed that the application's background server
processes log alarming, error-level "pending task" teardown warnings during
shutdown of MCP-related servers, even though the shutdown itself succeeds.
The underlying cause is that some shutdown-related work started by these
servers' background processing may still be wrapping up at the moment the
server is told it has stopped; if that work is not given a chance to finish
or be cleanly cancelled first, it is later flagged as abandoned and a
warning is logged. This affects:

- The application's embedded MCP server.
- The application's embedded metrics server.
- The integration test helper that spins up a live MCP server for tests.

The suggested remediation (per the Jira ticket) is to "await transport
shutdown in test harness" — i.e., ensure that any outstanding shutdown work
for a server is properly allowed to complete or be cancelled before that
server's shutdown is considered finished, both in normal application
operation and in the test harness that mimics it.

### Scope

In scope:
- Shutdown/teardown behavior of the MCP server, metrics server, and the
  live MCP server test helper — specifically, ensuring any outstanding
  shutdown work for a server is allowed to complete or be cancelled before
  that server's shutdown is considered finished.
- Verifying, via the test suite, that the previously observed warnings no
  longer occur.

Out of scope:
- Any change to how the servers start, bind, serve requests, or report
  status/errors.
- Any change to transport protocol behavior (SSE vs. streamable HTTP)
  visible to MCP clients.
- Broader background-processing architecture changes unrelated to shutdown.

### Constraints and Assumptions

- Programming language: Python (existing codebase convention).
- The fix must work uniformly across the MCP server, metrics server, and
  test harness, since all three independently manage their own background
  shutdown process.
- The underlying cause is specific to one kind of in-flight shutdown
  operation used internally by the servers' transport handling, but the
  remediation should generically cover any outstanding shutdown work, not
  special-case that one situation, so it also protects against similar
  warnings arising from other causes in the future.
- No new external dependencies should be required.
- Existing public behavior, return values, and error-reporting paths for
  server start/stop must remain unchanged; only internal teardown sequencing
  changes.

### Main Entities

- **MCP Server** (business entity: the application's Model Context Protocol
  server) — runs as a background process, must shut down cleanly when
  stopped or when startup fails.
- **Metrics Server** — runs as a background process, must shut down
  cleanly when stopped or when startup fails.
- **Live MCP Test Server** (test harness double) — a test-only stand-in for
  the MCP server, used by integration tests, must mirror the same clean
  shutdown behavior so tests do not surface noise unrelated to what they are
  testing.
- **In-Flight Shutdown Operation** — a piece of shutdown-related work that
  may still be in progress when a server is told to stop; must be allowed
  to complete, or be cleanly cancelled, before the server is considered
  fully stopped, rather than being abandoned.

## Q&A

- Q: Is PYPOST-726 the same work item as PYPOST-686?
  A: PYPOST-726 is a "Debt" ticket created from audit finding R-P3-003
     (labels: audit, tech-debt, testing) and its summary explicitly
     references "[PYPOST-686]" — i.e., PYPOST-726 is the actionable
     follow-up ticket for the issue originally raised under PYPOST-686.
     Confirmed via `jira_get_issue` on PYPOST-726.
- Q: Does an implementation already exist?
  A: Yes — at the start of this task there is already an uncommitted
     working-tree change that appears to address this remediation at the
     business level: outstanding shutdown work is given a chance to finish
     or be cancelled before each affected server (and the test harness's
     live MCP test server) considers its shutdown complete. This
     requirements document derives its acceptance criteria from the
     business/functional intent of that existing change, without
     prescribing how it is implemented; subsequent steps (architecture,
     development) should validate/formalize the existing change against
     these requirements rather than assuming no work has been done yet.

## Approval

- Auto-approved under autonomous sprint-task-runner mode (no human reviewer
  available in this run); review and approval step normally required by
  `.cursor/rules/10-requirements.mdc` was performed by the runner itself
  acting on the reviewer's verdict, not by a human stakeholder.
