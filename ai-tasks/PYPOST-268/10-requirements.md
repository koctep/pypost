# PYPOST-268 / PYPOST-271: Unit tests for HTTPClient._prepare_request_kwargs

## Goals

`HTTPClient._prepare_request_kwargs` was extracted in PYPOST-30 to make request-kwarg
assembly testable without mocking the full HTTP transport. The helper remains uncovered by
direct unit tests; existing coverage only exercises it indirectly through `send_request`.
Developers need fast, focused tests that verify template rendering and body serialization
without session mocks.

## User Stories

- As a **maintainer**, I want unit tests that call `_prepare_request_kwargs` directly so I can
  change URL/header/body rendering logic without running the full send path.
- As a **contributor**, I want regression tests for JSON, YAML-as-JSON, and raw body branches
  so body-type mistakes are caught before integration tests.

## Definition of Done

- A dedicated test class calls `_prepare_request_kwargs` in isolation (no `session.request`).
- Coverage includes: URL (template and `rendered_url`), headers (including Authorization),
  params, default kwargs (`stream`, `timeout`), JSON/YAML/text body branches, whitespace body,
  `ResolvedRequestFields`, and YAML conversion failure (`ExecutionError` BODY).
- All new tests use the module-level `pytestmark` timeout (already present in
  `tests/test_http_client.py`).
- `make test` passes.
- PYPOST-268 and PYPOST-271 are satisfied by the same change set.

## Task Description

PYPOST-30 noted that `_prepare_request_kwargs` is easily testable but lacked dedicated tests
(PYPOST-268). PYPOST-271 tracks the follow-up to add those tests. Scope is test-only; no
production code changes required unless a defect is found.

## Q&A

- **Q:** Why two Jira issues? **A:** PYPOST-268 records the gap from PYPOST-30 review;
  PYPOST-271 is the explicit follow-up task. Both close with this work.
