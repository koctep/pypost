# PYPOST-45 Tech Debt Review

## Summary

PYPOST-45 successfully removes the `template_service` module-level singleton and replaces it with
constructor injection across `HTTPClient`, `RequestService`, and `MCPServerImpl`. All acceptance
criteria are met. No new tech debt was introduced. Two minor pre-existing issues are surfaced below
for awareness.

---

## Verdict: Accepted — No Blocking Debt

The implementation follows the architecture exactly. Code is clean, tests pass, and the refactor
achieves its stated goal without side-effects.

---

## Findings

### TD-1 — Trailing whitespace in `http_client.py` (Pre-existing, Low)

**File**: `pypost/core/http_client.py`, lines 34, 51, 57
**Type**: Style / pre-existing
**Impact**: None functional. May generate noise in future diffs.
**Recommendation**: Clean up in a dedicated style-only commit or via a pre-commit lint hook.
**Owner**: Whoever next touches `http_client.py`.

---

### TD-2 — `logger` placement in `mcp_server_impl.py` (Pre-existing, Low)

**File**: `pypost/core/mcp_server_impl.py`, lines 5–6
**Observation**: `logger = logging.getLogger(__name__)` is declared between two `import` blocks
(after `from starlette.applications import Starlette` and before `from starlette.responses import
Response`). PEP 8 and the project's own style place module-level assignments after all imports.
**Type**: Style / pre-existing (not introduced by PYPOST-45)
**Impact**: None functional.
**Recommendation**: Move `logger` after all imports in a future cleanup pass. No immediate action
required.

---

### TD-3 — Autonomous-default creates separate `TemplateService` instances per class (Design note)

**Observation**: When callers use the default (`MCPServerImpl(metrics=m)`), a single
`TemplateService` instance is created in `MCPServerImpl.__init__` and propagated down to
`RequestService` and then `HTTPClient`. This is correct and intentional per the architecture.

However, if a caller constructs `RequestService` or `HTTPClient` directly without passing a
`TemplateService`, each gets its own `jinja2.Environment`. This is an accepted trade-off
(documented in `20-architecture.md` — "autonomous default pattern") and is not a bug. It is
noted here for future maintainers who may expect a shared environment across independently
constructed instances.

**Risk**: Low. `jinja2.Environment` is stateless by default in this codebase (no custom
globals/filters are added after construction).
**Recommendation**: Document the autonomous-default pattern in the `TemplateService` class
docstring if sharing becomes a concern in future.

---

## Acceptance Criteria Verification

| Criterion | Status |
|---|---|
| AC-1: no `from pypost.core.template_service import template_service` in source | PASS |
| AC-2: no `template_service = TemplateService()` in `template_service.py` | PASS |
| AC-3: all three classes store `self._template_service` | PASS |
| AC-4: all existing tests pass without modification | PASS (19/19) |
| AC-5: new test confirms injected mock is invoked in `send_request` | PASS |

---

## Test Coverage

- **19 tests** across `tests/test_http_client.py` and `tests/test_request_service.py`, all passing.
- 4 new tests added (2 per file) exercising the injection path and the default-creation path.
- No regression on `tests/test_template_service.py` (unchanged, passes independently).
