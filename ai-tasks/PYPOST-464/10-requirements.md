# PYPOST-464: Add explicit masking metric tests for empty vs non-empty hidden_keys

## Goals

PYPOST-446 introduced `hidden_value_masks_applied_total`, incremented in `RequestService.execute`
only when `hidden_key_count > 0`. Existing unit tests in `TestRequestServiceHistory` assert the
`track_hidden_value_mask_applied` mock is called or not called, but do not verify the Prometheus
counter through a real `MetricsManager` registry scrape.

This task closes that observability test gap. The primary deliverable is **regression protection**
for metric emission rules established by PYPOST-446. Product behavior should remain unchanged.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want automated checks that scrape the real Prometheus counter so metric
  wiring regressions are caught without relying solely on mock assertions.
- As a **quality reviewer**, I want an explicit negative test confirming the counter is **not**
  incremented when `hidden_keys` is empty or absent, matching production guard logic.
- As a **quality reviewer**, I want a positive test confirming the counter **is** incremented
  when `hidden_keys` is non-empty during history write.

## Definition of Done

1. Automated tests use a real `MetricsManager` and scrape its registry (same pattern as
   `tests/test_storage_environments.py`).
2. Tests assert `hidden_value_masks_applied_total{surface="history"}` is **absent** from scraped
   output when `hidden_keys` is empty (`set()`) or `None`.
3. Tests assert the counter equals **1.0** when `hidden_keys` is non-empty and history is
   recorded via `RequestService.execute`.
4. Tests exercise `RequestService.execute` with HTTP mocked at the boundary (same pattern as
   `tests/test_history_masking_e2e.py` / `tests/test_request_service.py`).
5. Coverage is **traceable** to the missing-coverage item in
   [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md) and Jira
   [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464).
6. **No product behavior change** — deliverable is test coverage only.

## Task Description

### Problem Statement

The masking metric guard (`if self._metrics and hidden_key_count > 0`) is covered by mock-based
unit tests but not by integration-style counter scrape tests. A refactor could break the guard or
counter registration without failing mock-only checks if the mock path diverged from production.

### In Scope

- Prometheus scrape tests for `hidden_value_masks_applied_total` with empty vs non-empty
  `hidden_keys`.
- `RequestService.execute` wiring with real `MetricsManager`, mocked HTTP, mocked history manager.

### Out of Scope

- New product features or changes to masking rules, history behavior, or metric definitions.
- Replacing existing mock-based unit tests in `tests/test_request_service.py` (they remain as
  fast unit coverage).
- History persistence/reload or History panel display ([PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462)).
- Refactoring history-recording logic ([PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463)).
- CI/local dependency provisioning ([PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465)).

## Functional Requirements

- The project must include automated tests that scrape a real `MetricsManager` registry after
  `RequestService.execute`.
- Empty or absent `hidden_keys` must not produce a `hidden_value_masks_applied_total` sample for
  `surface="history"`.
- Non-empty `hidden_keys` must increment the counter to `1.0` for `surface="history"`.

## Non-Functional Requirements

- **Maintainability:** follow existing `_scrape_metrics` and `RequestService.execute` test patterns.
- **Stability:** adding tests must not alter production masking or metric behavior.
- **Performance:** tests run in isolation with a fresh `MetricsManager` per case.

## Constraints and Assumptions

- Prometheus counters with value zero are omitted from scrape output; negative tests assert
  absence of the labeled metric line.
- `RequestService` requires a history manager to reach the metric emission block; HTTP is mocked.

## Main Entities and Interactions (Business View)

- **RequestService** — orchestrates execute flow and emits masking metrics at history write.
- **MetricsManager** — owns `hidden_value_masks_applied_total` counter.
- **hidden_keys** — set of environment variable names marked hidden; cardinality drives metric guard.

Interaction under test:

1. Execute request with variables and optional `hidden_keys`.
2. History recording path evaluates `hidden_key_count`.
3. Metric counter increments only when count > 0.
4. Test scrapes registry and asserts counter presence and value.

## Q&A

- **Is this a feature or test task?**
  Test-coverage debt task; behavior unchanged.
- **Why scrape metrics instead of mocks?**
  Validates real counter registration and label values in the Prometheus registry.
- **What is the boundary with PYPOST-462?**
  PYPOST-462 owns persistence/reload/UI journey; PYPOST-464 owns metric counter rules only.
- **Source of this task?**
  Follow-up from [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md).
