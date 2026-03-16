# PYPOST-45 Code Cleanup

## Summary

All code changes for PYPOST-45 are complete. No cleanup was required beyond the
implementation itself, as the architecture was followed exactly.

## Changes Made

### `pypost/core/template_service.py`
- Removed module-level global `template_service = TemplateService()` (lines 35–36).
- Class definition is unchanged.

### `pypost/core/http_client.py`
- Replaced `from pypost.core.template_service import template_service` with
  `from pypost.core.template_service import TemplateService`.
- Added `template_service: TemplateService | None = None` parameter to `__init__`.
- Added `self._template_service` assignment with autonomous default pattern.
- Replaced all 6 bare `template_service.render_string(...)` calls with
  `self._template_service.render_string(...)`.

### `pypost/core/request_service.py`
- Replaced `from pypost.core.template_service import template_service` with
  `from pypost.core.template_service import TemplateService`.
- Added `template_service: TemplateService | None = None` parameter to `__init__`.
- Added `self._template_service` assignment with autonomous default pattern.
- Forwarded `template_service=self._template_service` to `HTTPClient(...)`.
- Replaced 2 bare `template_service.render_string(...)` calls in `_execute_mcp`
  with `self._template_service.render_string(...)`.

### `pypost/core/mcp_server_impl.py`
- Replaced `from pypost.core.template_service import template_service` with
  `from pypost.core.template_service import TemplateService`.
- Added `template_service: TemplateService | None = None` parameter to `__init__`.
- Added `self._template_service` assignment with autonomous default pattern.
- Forwarded `template_service=self._template_service` to `RequestService(...)`.
- Replaced 1 bare `template_service.parse(content)` call in `_extract_mcp_variables`
  with `self._template_service.parse(content)`.

### `tests/test_http_client.py`
- Appended `TestHTTPClientInjection` with 2 tests:
  - `test_injected_template_service_is_used_not_default`
  - `test_no_injection_creates_own_template_service`

### `tests/test_request_service.py`
- Appended `TestRequestServiceInjection` with 2 tests:
  - `test_injected_template_service_forwarded_to_http_client`
  - `test_no_injection_creates_own_template_service`

## Quality Checks

- All 19 tests pass (`pytest tests/test_http_client.py tests/test_request_service.py`).
- No global `template_service` object remains anywhere in the codebase.
- Existing call sites (`MCPServerManager`, `RequestWorker`) required no changes
  because the new parameter defaults to `None`.
- Code follows PEP 8 and stays within the 100-character line limit.
- No trailing whitespace; single final newline on all modified files.
