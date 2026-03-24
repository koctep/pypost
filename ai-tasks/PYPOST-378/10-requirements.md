# PYPOST-378: Requirements — MetricsManager & template_service DIP Violations

## Background

**Source:** `ai-tasks/PYPOST-40/60-tech-debt.md` (audit findings F2, F3, R2, R3)
**Priority:** High
**Type:** Tech Debt (DIP violation)

The PYPOST-40 SOLID audit identified two module-level singleton/global patterns that violate the
Dependency Inversion Principle (DIP):

- **F2** — `MetricsManager()` was used as a module-level singleton, accessed directly throughout the
  codebase (`main_window`, `request_editor`, `response_view`, `request_service`, `http_client`,
  `mcp_server_impl`). No injection. Hard to mock or swap.
- **F3** — `template_service` global at `template_service.py:36` was a module-level singleton used
  in `http_client`, `request_service`, and `mcp_server_impl`. No injection. Hard to mock.

### Work Already Completed

- **PYPOST-44** — Replaced `MetricsManager` singleton with constructor injection. `main.py` now
  creates one `MetricsManager` instance and passes it down via constructors.
- **PYPOST-45** — Replaced the `template_service` global with a `TemplateService` class that
  accepts optional injection in `HTTPClient`, `RequestService`, and `MCPServerImpl`.

---

## Problem Statement

Despite PYPOST-44 and PYPOST-45, the `TemplateService` dependency injection is **incomplete**:
the composition root (`main.py`) never creates a `TemplateService` instance. The dependency is
not propagated through all callers. As a result, `TemplateService` instances are created
internally as silent fallbacks in several classes, which is still a DIP violation.

### Remaining Gaps

| Component | Gap | File |
|-----------|-----|------|
| `main.py` | Does not create a `TemplateService` instance | `pypost/main.py` |
| `MCPServerManager` | Does not accept or propagate `template_service` | `pypost/core/mcp_server.py:18` |
| `MCPServerImpl` | Falls back to `TemplateService()` when not injected | `pypost/core/mcp_server_impl.py:29` |
| `RequestWorker` | Does not accept or propagate `template_service` | `pypost/core/worker.py:20` |
| `RequestService` | Falls back to `TemplateService()` when not injected | `pypost/core/request_service.py:39` |
| `HTTPClient` | Falls back to `TemplateService()` when not injected | `pypost/core/http_client.py:27` |
| `TabsPresenter` | Does not pass `template_service` to `RequestWorker` | `pypost/ui/presenters/tabs_presenter.py:316` |

The `MetricsManager` injection is **complete**: one instance is created in `main.py`, injected
into `MainWindow`, and propagated through `MCPServerManager`, `MCPServerImpl`, `RequestService`,
`HTTPClient`, `TabsPresenter`, and `RequestWorker` correctly.

---

## Requirements

### REQ-1: Single TemplateService instance at composition root

`main.py` MUST create exactly one `TemplateService()` instance and pass it to `MainWindow` via
constructor.

### REQ-2: MainWindow must accept and propagate TemplateService

`MainWindow.__init__` must accept `template_service: TemplateService` and pass it to
`MCPServerManager` and `TabsPresenter` (or whatever presenter creates `RequestWorker`).

### REQ-3: MCPServerManager must accept and propagate TemplateService

`MCPServerManager.__init__` must accept `template_service: TemplateService` and pass it to
`MCPServerImpl`.

### REQ-4: RequestWorker must accept and propagate TemplateService

`RequestWorker.__init__` must accept `template_service: TemplateService | None = None` and pass
it to `RequestService`.

### REQ-5: Remove silent TemplateService fallback creation

The `| None` fallback that creates a new `TemplateService()` instance internally MUST be
removed from `HTTPClient`, `RequestService`, and `MCPServerImpl`. Once the injection chain is
complete, these components should require `template_service` to be provided (or accept `None`
without creating a fallback, relying on the callers to always inject it).

> **Note:** Keeping `| None = None` with no internal creation is acceptable for test ergonomics,
> but the fallback `TemplateService()` creation must be removed.

### REQ-6: TabsPresenter must propagate TemplateService to RequestWorker

`TabsPresenter` must store the injected `template_service` and pass it when constructing
`RequestWorker` (at `tabs_presenter.py:316`).

---

## Acceptance Criteria

1. Exactly one `TemplateService` instance exists at runtime, created in `main.py`.
2. No internal `TemplateService()` fallback construction in `HTTPClient`, `RequestService`, or
   `MCPServerImpl`.
3. The full injection chain is unbroken:
   `main.py` → `MainWindow` → `MCPServerManager` → `MCPServerImpl` → `RequestService` → `HTTPClient`
   `main.py` → `MainWindow` → `TabsPresenter` → `RequestWorker` → `RequestService` → `HTTPClient`
4. All existing tests pass without modification.
5. Unit tests can inject a mock/stub `TemplateService` without patching module globals.

---

## Out of Scope

- Introducing an abstract `TemplateServiceProtocol` interface (possible future improvement, not
  required here).
- Introducing an abstract `MetricsProtocol` interface (separate concern, not blocked by this
  ticket).
- Any changes to `MetricsManager` injection (already complete via PYPOST-44).
- Splitting `MetricsManager` into `MetricsRegistry` + `MetricsServer` (PYPOST-49).

---

## Affected Files

| File | Change Type |
|------|-------------|
| `pypost/main.py` | Add `TemplateService()` instantiation, pass to `MainWindow` |
| `pypost/ui/main_window.py` | Accept `template_service` parameter, propagate to presenters |
| `pypost/core/mcp_server.py` | Accept `template_service`, pass to `MCPServerImpl` |
| `pypost/core/mcp_server_impl.py` | Remove `TemplateService()` fallback creation |
| `pypost/core/worker.py` | Accept `template_service`, pass to `RequestService` |
| `pypost/core/request_service.py` | Remove `TemplateService()` fallback creation |
| `pypost/core/http_client.py` | Remove `TemplateService()` fallback creation |
| `pypost/ui/presenters/tabs_presenter.py` | Store and propagate `template_service` to `RequestWorker` |
