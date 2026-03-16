# PYPOST-45 Requirements: Replace `template_service` Global with Constructor Injection

## Overview

**Ticket**: PYPOST-45 (Debt, High Priority)
**Source**: PYPOST-40 audit finding R3
**Summary**: The module-level singleton `template_service = TemplateService()` in
`pypost/core/template_service.py` is imported directly by `HTTPClient`, `RequestService`,
and `MCPServerImpl`. This global coupling violates the Dependency Inversion Principle, makes
unit testing harder, and prevents per-instance or configurable template engine behaviour.

---

## Problem Statement

### Current State

`pypost/core/template_service.py` exposes a module-level global:

```python
# line 36
template_service = TemplateService()
```

Three production modules import this global directly:

| File | Import | Usage locations |
|---|---|---|
| `pypost/core/http_client.py` | `from pypost.core.template_service import template_service` | lines 26, 30–31, 36–37, 40, 145 |
| `pypost/core/request_service.py` | `from pypost.core.template_service import template_service` | lines 33–34 |
| `pypost/core/mcp_server_impl.py` | `from pypost.core.template_service import template_service` | line 132 |

### Issues

1. **Hidden dependency** — consumers do not declare `TemplateService` in their constructor
   signatures; the dependency is invisible to callers and DI containers.
2. **Hard to test** — tests must either import the global (coupling tests to module state) or
   monkey-patch the module, making test isolation fragile.
3. **Singleton side-effects** — a single shared `jinja2.Environment` means any mutation
   (e.g. adding globals, filters) affects all consumers simultaneously.
4. **Violates SOLID R3 finding from PYPOST-40** — dependency should flow through constructors.

---

## Requirements

### REQ-1 — Remove the global singleton

- Remove `template_service = TemplateService()` (line 36) from
  `pypost/core/template_service.py`.
- The `TemplateService` class definition must remain unchanged.
- No other file should import the bare `template_service` name from this module after
  this change.

### REQ-2 — Inject `TemplateService` into `HTTPClient`

- `HTTPClient.__init__` must accept a new optional parameter:
  `template_service: TemplateService | None = None`.
- When `None` is provided, `HTTPClient` creates its own `TemplateService()` as the default.
- All internal usages of the old module-level `template_service` must be replaced with
  `self._template_service`.
- The existing `metrics` parameter and behaviour must be unchanged.

### REQ-3 — Inject `TemplateService` into `RequestService`

- `RequestService.__init__` must accept a new optional parameter:
  `template_service: TemplateService | None = None`.
- When `None` is provided, `RequestService` creates its own `TemplateService()` as the default.
- `RequestService` must pass `self._template_service` when constructing `HTTPClient`:
  `self.http_client = HTTPClient(metrics=self._metrics, template_service=self._template_service)`.
- All internal usages of the module-level `template_service` in `_execute_mcp` must be
  replaced with `self._template_service`.

### REQ-4 — Inject `TemplateService` into `MCPServerImpl`

- `MCPServerImpl.__init__` must accept a new optional parameter:
  `template_service: TemplateService | None = None`.
- When `None` is provided, `MCPServerImpl` creates its own `TemplateService()` as the default.
- `MCPServerImpl` must pass `self._template_service` when constructing `RequestService`:
  `self.request_service = RequestService(metrics=self._metrics, template_service=self._template_service)`.
- The usage of `template_service.parse(content)` in `_extract_mcp_variables` must be
  replaced with `self._template_service.parse(content)`.

### REQ-5 — Callers require no mandatory change

- `MCPServerManager` instantiates `MCPServerImpl(metrics=metrics)`. Because the new
  parameter defaults to `None` (auto-creates), this call must continue to work without
  modification.
- `RequestWorker` instantiates `RequestService(metrics=metrics)`. Same — must work
  without modification.
- Both callers **may optionally** be updated to pass an explicit `TemplateService` if
  desired, but this is not required by this ticket.

### REQ-6 — Existing tests must pass unmodified

- `tests/test_template_service.py` — no changes needed; it instantiates `TemplateService`
  directly.
- `tests/test_http_client.py` — `HTTPClient()` and `HTTPClient(metrics=MagicMock())`
  invocations must continue to work.
- `tests/test_http_client_sse_probe.py` — `HTTPClient()` invocations must continue to work.
- `tests/test_request_service.py` — `RequestService(metrics=MagicMock())` invocations must
  continue to work.

### REQ-7 — New unit tests for injection

- Add tests verifying that a custom `TemplateService` passed to `HTTPClient` is used
  (not a freshly-created default), demonstrating the injection works.
- Add tests verifying that a custom `TemplateService` passed to `RequestService` is
  forwarded to `HTTPClient`.
- Test coverage must not decrease.

---

## Affected Files

| File | Change Type |
|---|---|
| `pypost/core/template_service.py` | Remove global singleton (line 36) |
| `pypost/core/http_client.py` | Add constructor parameter, replace global usages |
| `pypost/core/request_service.py` | Add constructor parameter, replace global usages, pass to `HTTPClient` |
| `pypost/core/mcp_server_impl.py` | Add constructor parameter, replace global usage, pass to `RequestService` |
| `tests/test_http_client.py` | Add injection tests (optional extend, not modify existing) |
| `tests/test_request_service.py` | Add injection tests (optional extend, not modify existing) |

---

## Out of Scope

- Changes to `TemplateService` internal implementation (`render_string`, `parse`).
- Adding a `TemplateService` parameter to `MCPServerManager` or `RequestWorker`
  (they may use the default).
- Replacing the `jinja2.Environment` with a different templating engine.
- Any changes to non-template rendering logic in the affected files.

---

## Acceptance Criteria

1. `grep -r "from pypost.core.template_service import template_service"` returns no matches.
2. `grep "template_service = TemplateService()" pypost/core/template_service.py` returns
   no matches.
3. All three classes (`HTTPClient`, `RequestService`, `MCPServerImpl`) store the injected
   (or default-constructed) instance as `self._template_service`.
4. All existing unit tests pass without modification.
5. At least one new test confirms that a mock/custom `TemplateService` injected into
   `HTTPClient` is actually invoked during `send_request`.
