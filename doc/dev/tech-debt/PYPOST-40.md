# Technical Debt for Task PYPOST-40 (SOLID Audit)

This task produced an audit report. The audit identified technical debt in the codebase; this
file summarizes follow-up items for developers.

## 1. MainWindow Decomposition

MainWindow (1040 LOC) has many responsibilities. Extract presenters: CollectionsPresenter,
TabsPresenter, EnvironmentPresenter. See [30-audit-report.md](../../../ai-tasks/PYPOST-40/30-audit-report.md) R1.

## 2. Dependency Injection

Replace MetricsManager singleton and template_service global with constructor injection. Pass
from main.py. See audit R2, R3.

## 3. Collection Loading

MainWindow loads collections from Storage directly in `load_collections()` but uses
RequestManager for CRUD. Unify: use RequestManager.reload_collections() and get_collections().
See audit R5.

## 4. Request Execution Protocol

RequestService, RequestWorker, MCPServerImpl create HTTPClient/RequestService directly. Introduce
protocols for testability. See audit R4, R9.

## Follow-up Tasks

- **Prerequisite:** PYPOST-52 — Add test coverage for refactoring safety (blocks P1)
- **P1:** PYPOST-43 (MainWindow), PYPOST-44 (MetricsManager), PYPOST-45 (template_service)
- **P2:** PYPOST-46 (HTTPClient protocol), PYPOST-47 (collection loading), PYPOST-48
  (item_type strategy), PYPOST-49 (MetricsManager split)
- **P3:** PYPOST-50 (StorageInterface), PYPOST-51 (ExecuteRequestProtocol)
- Consider automated audit tooling (radon, pylint) in CI.
