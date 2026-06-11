# PYPOST-382: Testability gaps — RequestService, HTTPClient, MainWindow

## Goals

The PYPOST-40 audit found that core request execution and the main window are difficult to
unit test because dependencies are constructed internally. Maintainers need documented patterns
and practical injection seams so tests can isolate behavior without network, MCP, or full Qt
startup.

A full dependency-inversion refactor is out of scope; this task delivers pragmatic improvements
that unblock unit testing today.

## User Stories

- As a maintainer, I want to inject a mock HTTP transport into `RequestService` so I can test
  orchestration logic without real network calls.
- As a maintainer, I want to inject a mock `requests.Session` into `HTTPClient` so transport
  tests do not patch attributes after construction.
- As a maintainer, I want documented patterns for testing `MainWindow` with mocked collaborators
  so new UI tests follow a consistent approach.
- As a developer, I want a single dev doc describing testability seams and example tests.

## Definition of Done

- Constructor injection seams added to `RequestService` (`http_client`, `mcp_client`) and
  `HTTPClient` (`session`) where feasible without breaking production callers.
- Unit tests demonstrate and verify the new seams.
- `doc/dev/testability.md` documents patterns for `RequestService`, `HTTPClient`, and
  `MainWindow`.
- Existing test suite passes.
- Remaining gaps (protocols, full MainWindow decomposition) recorded as follow-up debt with
  links to existing Jira tickets.

## Task Description

Follow-up from `ai-tasks/PYPOST-40/60-tech-debt.md` — "Testability gaps". Metrics and
TemplateService injection were addressed in PYPOST-44/PYPOST-378; this task closes the audit
item for transport and UI testability documentation.

## Q&A

- **Q:** Full DI container or protocol refactor? **A:** Out of scope — defer to PYPOST-46,
  PYPOST-379, PYPOST-43.
- **Q:** Inject `RequestService` into `RequestWorker`? **A:** Out of scope for this ticket;
  document current mock-after-construct pattern and link PYPOST-379.
- **Q:** E2E MainWindow tests? **A:** Out of scope — document presenter patching patterns
  already used in `tests/test_main_window.py`.
