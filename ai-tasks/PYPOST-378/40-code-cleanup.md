# PYPOST-378: Code Cleanup

## Summary

All code changes follow the architecture exactly. No structural issues were found during
implementation. Cleanup actions below are limited to test corrections required by the removal of
silent fallback construction.

---

## Changes Made

### Production code (8 files)

| File | Change |
|------|--------|
| `pypost/main.py` | Import `TemplateService`; create single instance; pass to `MainWindow` |
| `pypost/ui/main_window.py` | Accept `template_service: TemplateService`; store; propagate to `MCPServerManager` and `TabsPresenter` |
| `pypost/core/mcp_server.py` | Accept `template_service: TemplateService | None = None`; pass to `MCPServerImpl` |
| `pypost/core/mcp_server_impl.py` | Remove `else: TemplateService()` fallback; assign directly from param |
| `pypost/core/worker.py` | Accept `template_service: TemplateService | None = None`; pass to `RequestService` |
| `pypost/core/request_service.py` | Remove `else: TemplateService()` fallback; assign directly from param |
| `pypost/core/http_client.py` | Remove `else: TemplateService()` fallback; assign directly from param |
| `pypost/ui/presenters/tabs_presenter.py` | Accept `template_service: TemplateService | None = None`; store as `self._template_service`; pass to `RequestWorker` |

### Test corrections (2 files)

Tests that called render paths without injecting a `TemplateService` were updated to inject
`TemplateService()` explicitly. Tests that asserted the old silent-fallback behaviour were
rewritten to assert the new correct behaviour (`_template_service is None`).

| File | Change |
|------|--------|
| `tests/test_http_client.py` | `TestHTTPClientSendRequest.setUp` injects `TemplateService()`; `test_no_injection_creates_own_template_service` renamed and rewritten to assert `_template_service is None` |
| `tests/test_request_service.py` | `TestRequestServiceMCP.setUp` and `TestRequestServiceHistory.setUp` inject `TemplateService()`; `test_no_injection_creates_own_template_service` renamed and rewritten to assert `_template_service is None` |

---

## Standards Compliance

- Line length: all lines ≤ 100 characters
- Encoding: UTF-8, LF line endings
- No trailing whitespace introduced
- No new abstractions, helpers, or unused imports added
- Only the 8 production files and 2 test files identified in the architecture were modified
