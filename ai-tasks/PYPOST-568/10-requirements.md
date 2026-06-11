# PYPOST-568: Analyze worker/presenter tests that log ERROR on expected failures

## Goals

PYPOST-567 catalogued 72 ERROR lines emitted during a green full-suite run. Many come from
tests that deliberately exercise failure paths (worker exceptions, retry exhaustion, delete
errors, request error dialogs). This task audits the highest-priority modules identified in
the inventory and documents whether each ERROR-emitting test has strong enough assertions to
avoid false-positive risk.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want a per-test audit of ERROR logs in worker and presenter modules
  so that I can tell intentional error-path noise from weak tests.
- As a **maintainer**, I want each audited test rated low/medium/high risk with assertion
  strength notes so that follow-up remediation can be prioritized.
- As a **team lead**, I want mitigation recommendations (caplog, allowlist, log level) so
  that PYPOST-571 CI guardrails can be scoped without re-reading test code.

## Definition of Done

- [x] Audit report covers all ERROR lines from focus modules in PYPOST-567 inventory:
      `test_worker.py`, `test_tabs_presenter.py`, `test_collection_tree_delete_metrics.py`,
      `test_retry.py`.
- [x] Each test lists logger, message pattern, risk rating, assertion strength, mitigation.
- [x] Top-down artifacts stored under `ai-tasks/PYPOST-568/`.
- [x] `doc/dev/testing.md` updated with brief guidance on error-path test logging.
- [x] Jira PYPOST-568 transitioned to Done with summary comment.

## Task Description

### Problem

Passing tests that emit ERROR logs obscure real regressions during log review and future CI
log-threshold gates. Worker, tabs presenter, collection-tree delete, and retry modules
account for a significant share of inventory ERROR lines. Some tests assert behavior via
mocked UI dialogs or metrics but never assert that the expected log line was emitted; others
may rely only on return values.

### Baseline

Source: `ai-tasks/PYPOST-567/inventory.csv` (2026-06-11 capture, 937 passed).

| Focus module | ERROR lines in inventory |
| --- | ---: |
| `tests/test_retry.py` | 12 |
| `tests/test_tabs_presenter.py` | 6 |
| `tests/test_collection_tree_delete_metrics.py` | 3 |
| `tests/test_worker.py` | 1 |
| **Total** | **22** |

### Functional requirements

1. Map each inventory ERROR row to its test function and production log site.
2. Read test source and classify assertion strength: **strong**, **moderate**, **weak**.
3. Assign risk: **low** (intentional path, strong assertions), **medium** (intentional but
   log-only signal), **high** (weak assertions or ambiguous intent).
4. Recommend mitigation: document-only, `caplog` assertion, pytest allowlist entry, or
   production log-level change (deferred).
5. Publish `error-path-test-audit.md` as the primary deliverable.

### Non-functional requirements

- Analysis-only — no test or production code changes in this task.
- Recommendations must be actionable for PYPOST-571 (allowlist) and optional caplog follow-ups.

### Out of scope

- Implementing caplog assertions or CI guardrails.
- Changing production log levels.
- Auditing modules outside the four focus test files.

## Q&A

| Question | Answer |
| --- | --- |
| Why these four files? | PYPOST-567 architecture notes them as downstream priority; they cover worker, UI error handling, delete metrics, and retry exhaustion. |
| What makes a test "strong"? | Asserts observable outcome (signal, metric, dialog mock, execution_error fields) tied directly to the failure being simulated. |
| What makes risk "medium"? | ERROR log is expected side effect but not asserted; real production ERROR could look identical in CI output. |
