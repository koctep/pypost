# PYPOST-378: Tech Debt Review

## Summary

PYPOST-378 closes the `TemplateService` DIP violation introduced by PYPOST-45. The
implementation is clean, minimal, and consistent with the `MetricsManager` injection
pattern already established in PYPOST-44. No new tech debt was introduced.

---

## Resolved Debt

| ID | Finding | Resolution |
|----|---------|------------|
| F3 | `TemplateService` created as silent fallback in `HTTPClient`, `RequestService`, `MCPServerImpl` | Fallback `else` branch removed from all three classes |
| R3 | No composition root for `TemplateService` | Single instance created in `main.py`, propagated via constructors |
| — | `MCPServerManager`, `RequestWorker`, `TabsPresenter` did not accept or thread `template_service` | All three updated to accept and propagate the parameter |

---

## Remaining / New Debt

### TD-1: No `TemplateServiceProtocol` interface (pre-existing, accepted)

**Severity:** Low
**File:** `pypost/core/template_service.py`

All consumers accept the concrete `TemplateService` type. There is no abstract interface,
making it impossible to substitute a different implementation (e.g. a non-Jinja2 renderer or
a test double that does not import Jinja2). The requirements explicitly defer this to a future
ticket; current test ergonomics are adequate because `TemplateService` is cheap to instantiate.

**Recommendation:** Create a `TemplateServiceProtocol` (structural subtyping via `typing.Protocol`)
when a second implementation is needed or when Jinja2 becomes an unwanted test dependency.

---

### TD-2: `template_service: TemplateService | None = None` — silent `None` risk (pre-existing, accepted)

**Severity:** Low
**Files:** `pypost/core/http_client.py`, `pypost/core/request_service.py`,
`pypost/core/mcp_server_impl.py`, `pypost/core/worker.py`, `pypost/ui/presenters/tabs_presenter.py`

Leaf classes store `self._template_service = template_service` where the value may be `None`.
Call sites that invoke `self._template_service.render_string(...)` unconditionally will raise
`AttributeError` at runtime if `template_service` was not injected. The production path is safe
(always injected from `main.py`), but a future caller that omits injection and exercises a render
path will get a late, opaque error.

**Recommendation:** When the `TemplateServiceProtocol` interface (TD-1) is introduced, make the
parameter required (remove `| None = None`) at the leaf level, forcing callers to inject
explicitly. Until then, the accepted risk is low: the composition root guarantees injection in
all production paths.

---

### TD-3: `MainWindow.template_service` is a public attribute (minor)

**Severity:** Very Low
**File:** `pypost/ui/main_window.py:33`

`self.template_service = template_service` stores the service as a public attribute. This is
consistent with how `self.metrics` is stored in the same class and is unlikely to cause issues
in practice. If access control becomes a concern, rename to `self._template_service`.

---

## Code Quality Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Correctness | ✓ Pass | All acceptance criteria met; injection chain complete |
| SOLID compliance | ✓ Pass | DIP violation removed; no new violations introduced |
| Test coverage | ✓ Pass | Two test files updated; fallback-behaviour tests rewritten |
| Observability | ✓ Pass | INFO at root, DEBUG at each propagation hop |
| Diff surface | ✓ Pass | Exactly 10 files touched, no unrelated changes |
| Line length / style | ✓ Pass | All lines ≤ 100 chars; LF endings; UTF-8 |

---

## Verdict

No blockers. The implementation follows the agreed architecture precisely. The three items
above are pre-existing or accepted trade-offs, not regressions introduced by this ticket.
