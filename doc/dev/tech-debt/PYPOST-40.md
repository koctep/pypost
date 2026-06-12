# Technical Debt for Task PYPOST-40 (SOLID Audit)

This task produced an audit report. The audit identified technical debt in the codebase; this
file summarizes follow-up items for developers.

## 1. MainWindow Decomposition

MainWindow (1040 LOC) has many responsibilities. Extract presenters: CollectionsPresenter,
TabsPresenter, EnvironmentPresenter. See [30-audit-report.md](../../../ai-tasks/PYPOST-40/30-audit-report.md) R1.

## 2. Dependency Injection

**MetricsManager singleton resolved in PYPOST-44** ([PYPOST-167](../../ai-tasks/PYPOST-167/70-dev-docs.md)):
`main.py` creates one instance and injects it; tracking consumers use `MetricsTrackerProtocol`.
**TemplateService global resolved in PYPOST-45.** See audit R2, R3 and
[testability.md](../testability.md).

## 3. Collection Loading

**Resolved in PYPOST-47.** UI reads collections via `RequestManager.get_collections()`; disk
reloads use `RequestManager.reload_collections()` only. See [collection_loading.md](../collection_loading.md).
See audit R5.

## 4. Metrics Module Split

**Resolved in PYPOST-49** (implemented in [PYPOST-75](../mcp_integration.md)). Counters live in
`MetricsRegistry`; uvicorn/MCP lifecycle lives in `MetricsServer`; `MetricsManager` remains the
injection facade. See [mcp_integration.md](../mcp_integration.md) and
[testability.md](../testability.md). See audit R7.

## 5. Storage Abstraction

**Resolved in PYPOST-50.** Persistence consumers depend on `StorageInterface`; `StorageManager`
remains the composition-root implementation. See [testability.md](../testability.md). See audit R8.

## 6. Request Execution Protocol

RequestService accepts optional `http_client` and `mcp_client` constructor injection (PYPOST-382).
RequestWorker and MCPServerImpl still create RequestService internally. Introduce protocols for
full testability. See [testability.md](../testability.md) and audit R4, R9.

## 7. Collection Item Type Dispatch

**Resolved in PYPOST-48.** `RequestManager` routes `delete_collection_item` and
`rename_collection_item` through `DEFAULT_COLLECTION_ITEM_STRATEGIES` instead of inline
`item_type` branching. See [testability.md](../testability.md). See audit R6.

## Follow-up Tasks

- **Prerequisite:** PYPOST-52 — Add test coverage for refactoring safety (blocks P1)
- **P1:** PYPOST-43 (MainWindow), PYPOST-44 (MetricsManager), PYPOST-45 (template_service)
- **P2:** PYPOST-46 (HTTPClient protocol), ~~PYPOST-47 (collection loading)~~,
  ~~PYPOST-48 (item_type strategy)~~, ~~PYPOST-49 (MetricsManager split)~~
- **P3:** ~~PYPOST-50 (StorageInterface)~~, PYPOST-51 (ExecuteRequestProtocol)
- Consider automated audit tooling (radon, pylint) in CI.
