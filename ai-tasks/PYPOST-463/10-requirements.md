# PYPOST-463: Refactor RequestService history-recording block

## Goals

The history-recording section inside `RequestService.execute` combines masking, entry
construction, metrics, and logging in one inline block. This makes the method harder to read
and maintain. The goal is to reduce complexity without changing behaviour.

## User Stories

- As a **maintainer**, I want history recording extracted into focused helpers so I can
  understand and change masking or observability independently.
- As a **developer**, I want existing history and masking tests to pass unchanged so the
  refactor does not regress sensitive-data handling.

## Definition of Done

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-1 | History field building is in a dedicated helper | `_build_history_entry` exists |
| AC-2 | Observability emission is in dedicated helpers | Masking and entry helpers exist |
| AC-3 | `execute()` delegates to a single history orchestrator | `_record_execution_history` |
| AC-4 | Behaviour unchanged | `tests/test_request_service.py` history tests pass |
| AC-5 | Masking metrics unchanged | `tests/test_history_masking_metrics.py` pass |

## Task Description

Follow-up from [PYPOST-446](https://pypost.atlassian.net/browse/PYPOST-446) tech-debt review.
Extract helper functions for history field construction and observability emission from the
inline block in `RequestService.execute`. Pure refactor — no new features or API changes.

## Q&A

- **Why refactor?** Reduce method complexity and improve maintainability of history recording.
- **Scope?** `pypost/core/request_service.py` only; existing tests are the regression guard.
