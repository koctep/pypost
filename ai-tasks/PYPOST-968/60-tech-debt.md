# PYPOST-968: Technical Debt Analysis

**Verdict:** SAFE FOR INDEPENDENT REVIEW. No PYPOST-968 blocker was found.

The implementation meets the selected acceptance outcome: the existing forced
dialog-settle companion now proves that `pypost.agent.ui_wait` emits DEBUG
`ui_wait_timeout` with `condition=forced_dialog_settle_timeout`, while every
pre-existing exception-diagnostic assertion remains intact. The change is
test-only and does not alter application behavior, logging volume, or public APIs.

## Shortcuts Taken

No temporary product or test workaround was introduced.

- The proof extends the existing forced-timeout scenario instead of adding a
  second live GUI session. This is the architecture's intended smallest scope
  and avoids duplicating modal setup.
- The capture block is limited to one logger and the existing helper call. It
  does not rely on global DEBUG configuration or live CLI output.
- The assertion matches stable contract fields only. It deliberately omits
  `waited_ms`, timestamps, ordering, and exact record count because those are
  scheduler-dependent diagnostics rather than acceptance behavior.

## Code Quality Issues

No task-owned code quality issue requires follow-up.

- `_UI_WAIT_LOGGER` gives the production logger a single local test identity.
- The condition string appears in both the helper call and assertion so the
  test clearly states the emitted contract. Extracting another constant would
  not materially improve this single scenario.
- The filtered `LogRecord` list follows existing repository precedent and
  keeps logger, numeric severity, event prefix, and condition checks explicit.
- One `caplog.at_level` block is used for the one logger under test, as required
  by `.cursor/lsr/do-testing.md`.

## Missing Tests

No acceptance-relevant test is missing.

| Scenario | Status |
| --- | --- |
| Forced timeout preserves step and modal diagnostics | Covered by existing assertions |
| Exact production logger emits DEBUG timeout event | Covered by PYPOST-968 |
| Timeout event identifies the forced condition | Covered by PYPOST-968 |
| Removal, rename, logger movement, or severity drift | Detected by the new assertion |
| Exact elapsed time, ordering, or event count | Intentionally not contractual |
| Golden Send parity and other timeout companions | Out of scope |
| User-visible Settings behavior | Unchanged and out of scope |

The changed module declares `pytest.mark.timeout(60)` for both collected tests,
and the forced internal wait is bounded at 0.05 seconds. There is no missing
explicit-timeout blocker. Other concurrently changed test modules in the worktree
are unrelated to PYPOST-968 and also retain explicit module timeout markers; no
ownership or baseline follow-up is duplicated here.

## Performance Concerns

None. The new work is an in-memory scan of a few captured `LogRecord` objects
after an already-existing 0.05-second forced wait. It adds no production work,
I/O, network call, metric, or repeated GUI scenario. Fresh module runs completed
both tests in approximately 0.8 seconds when the local process exited cleanly.

## Architecture Deviations

None.

- The implementation extends the named existing companion in place.
- DEBUG capture surrounds only `run_product_dialog_settle`.
- Exact logger, numeric DEBUG severity, event prefix, and stable condition are
  verified through `LogRecord` APIs.
- Existing exception checks and modal fail-closed cleanup remain unchanged.
- Production wait, lifecycle, helper, golden Send, and monitoring code were not
  modified.

## Hardcoded Values

No problematic hardcoded value was introduced.

- `"pypost.agent.ui_wait"`, `"ui_wait_timeout "`, and
  `"forced_dialog_settle_timeout"` are intentional contract identifiers.
- `FORCED_SETTLE_TIMEOUT_S = 0.05` and module `timeout(60)` predate this task and
  provide the deterministic internal trigger plus outer hang backstop.

## Follow-up Tasks

### NON-BLOCKER

#### TD-1: Diagnose intermittent post-PASS Qt teardown SIGSEGV

- **Priority:** Low.
- **Action:** Capture a native backtrace and isolate modal/session teardown if
  the crash reproduces on a supported CI interpreter or continues locally.
- **Evidence:** The assertions finish as PASS before the crash, the `caplog`
  context has already exited, and two of three fresh independent module runs
  exited cleanly. Linux CI uses Python 3.11/3.13, while the crash was observed
  on macOS Python 3.14. Predecessor tasks document the same Qt/PySide modal
  teardown lineage.
- **Classification:** This is not evidence that the PYPOST-968 logging contract
  is broken, incomplete, or unsafe.
- **Jira:** [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040)
  (8 story points). The closed
  [PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) was checked as
  lineage and is not an exact duplicate.

This follow-up is intentionally narrow. Repository-wide SOLID snapshot drift,
AI-task artifact-baseline drift, and mypy-baseline drift are concurrent owners'
work and are not PYPOST-968 debt.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions or crutches | None |
| Code quality defect | None |
| Missing acceptance test | None |
| Missing explicit pytest timeout | **None** — module `timeout(60)` |
| Unbounded internal wait | None — forced wait is 0.05 seconds |
| Performance regression | None |
| Architecture deviation | None |
| Problematic hardcoded value | None |
| Product behavior or safety regression | None |
| Merge/release blocker | **None** |

The intermittent native teardown exit is retained as Low-priority, non-blocking
debt because it affects local test-process reliability, but it is not caused by
the test's logging assertion on available evidence and does not invalidate the
accepted observability behavior. Step 7 remains in progress until independent
review passes.
