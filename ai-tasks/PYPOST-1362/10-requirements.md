# PYPOST-1362: Stabilize failed-bind registry test against thread cleanup race

## Goals

CI and developers must be able to trust that a failed bind for one named MCP server
instance is reported only for that instance, without flaky “still running” false
positives after the bind failure. The business need is reliable regression coverage for
requested-instance isolation so unrelated instances are not wrongly treated as failed or
still running when only one bind was requested and failed.

## User Stories

- As a developer running the registry suite, I want the failed-bind isolation check to
  pass consistently so I can rely on green CI without intermittent false failures.
- As a maintainer of MCP server lifecycle behavior, I want failed-bind outcomes to reflect
  a settled “not running” state for the requested instance so operators are not misled by
  transient post-failure liveness.
- As a reviewer of multi-instance registry behavior, I want isolation guarantees preserved:
  a failed bind on one named instance must not imply failure or downtime for other
  instances that were not requested.

## Definition of Done

- The failed-bind isolation scenario for a single requested instance is deterministic under
  normal suite load (no flaky “still running” after a documented bind failure).
- After a failed bind for the requested instance, that instance is observably not running
  once the failure outcome is reported; other instances retain their prior isolation
  expectations.
- Lifecycle assertions are not weakened: the suite still requires “not running” after
  failed bind for the requested instance (no removal or softening of that check).
- Waiting for cleanup, if any, is bounded (no unbounded sleeps).
- Programming language for this task is Python.
- Target coverage node remains:
  `tests/test_mcp_server_registry.py::test_failed_bind_is_reported_for_only_the_requested_instance`
  (plus any adjacent deterministic helpers required for the same behavior).

## Task Description

During PYPOST-1354 full `make check`, the registry test that asserts a failed bind is
reported only for the requested instance failed intermittently:
`assert not registry.manager_for("beta-server").is_running()` was true when it should be
false after a port-busy bind failure. The same assertion reproduced at the baseline
commit. Narrowed retries sometimes passed, indicating a race between the startup-failure
signal and actual server-thread cleanup relative to immediate `is_running` checks.

Scope is to confirm the intended lifecycle semantics for failed bind (failure reported,
requested instance ends not running, other instances unaffected) and to make coverage
deterministic with bounded cleanup waiting—without weakening lifecycle assertions or
introducing unbounded sleeps.

## Q&A

- Q: Why fix this rather than skip/xfail the test?
  A: The isolation guarantee is a product regression signal; skipping would hide real
  lifecycle races. The test must stay strict and become deterministic.
- Q: Is weakening `is_running` after failure acceptable?
  A: No. The assertion that the failed instance is not running must remain; only race
  timing relative to cleanup may be addressed.
- Q: Implementation language?
  A: Python (existing registry and test suite).
