# PYPOST-143: TemplateService lifecycle architecture

## Problem

Original PYPOST-18 debt: `template_service = TemplateService()` at module scope coupled consumers
to a hidden singleton. Subsequent tickets removed the global and threaded injection, but the
lifecycle contract was spread across commits without a single design reference.

## Accepted design (2026-06)

Three coexisting patterns — intentional, not inconsistent:

### 1. Composition-root singleton (production)

```
main.py
  template_service = TemplateService(metrics=metrics_manager)
  MainWindow(template_service=template_service)
    ├─ MCPServerManager → MCPServerImpl → RequestService → HTTPClient
    └─ TabsPresenter → RequestWorker → RequestService → HTTPClient
```

Exactly one metrics-aware instance at runtime. All hops share the same `id()` and Jinja2
`Environment`.

### 2. Constructor injection seams (tests and partial graphs)

| Class | Parameter | When omitted |
| --- | --- | --- |
| `HTTPClient` | `template_service` | Creates local `TemplateService()` |
| `RequestService` | `template_service` | `None` on self; masking policy gets local instance |
| `MCPServerImpl` | `template_service` | Forwards to `RequestService` chain |
| `MainWindow` | `template_service` | **Required** in production |

Tests inject `TemplateService()` or `MagicMock()` at the leaf under test. See
`tests/test_http_client.py` (`TestHTTPClientInjection`), `tests/test_request_service.py`
(`TestRequestServiceInjection`), `tests/test_mcp_server_impl.py`.

### 3. UI hover module instance (exception)

`pypost/ui/widgets/mixins.py`:

- Module-level `_hover_template_service = TemplateService()`
- `VariableHoverHelper._template_service` class property (metaclass) for test assignment
- `VariableHoverResolver.set_metrics()` rebuilds instance when metrics are wired

Rationale: hover resolution is invoked from mixins without an injected service handle. Patching
the class property is the established test pattern (`tests/test_variable_hover.py`).

## Rejected alternatives

| Alternative | Why not now |
| --- | --- |
| DI container (injector, dependency-injector) | Overhead exceeds benefit for ~10 call sites |
| Restore module global | Violates DIP; closed in PYPOST-45 |
| Require `template_service` everywhere (no fallbacks) | Test ergonomics regression; track separately |

## Files touched (documentation only)

| File | Change |
| --- | --- |
| `doc/dev/template_service.md` | Lifecycle and test-seam section |
| `doc/dev/testability.md` | TemplateService summary + links |
| `doc/dev/solid_audit.md` | PYPOST-143 closure |
| `ai-tasks/PYPOST-18/40-tech-debt.md` | Mark global debt resolved |

## Verification

- `make test` — full suite
- Grep: no `template_service = TemplateService()` at module scope in `pypost/core/template_service.py`
