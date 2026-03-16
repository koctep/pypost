# PYPOST-44: Tech Debt Review

## Summary

PYPOST-44 successfully removes the `MetricsManager` singleton pattern and replaces it with
constructor injection across the full object graph. All 103 tests pass with no regressions.
This document records residual tech debt and recommendations for future work.

---

## 1. Debt Resolved

| Item | Status |
|------|--------|
| Hidden global state via `MetricsManager.__new__` singleton | Eliminated |
| `MetricsManager()` calls scattered across 9 production modules | Eliminated |
| Test patching via `patch("pypost.core.*.MetricsManager")` | Eliminated |
| Lifecycle print statements in metrics module | Replaced with structured logging |
| Silent exceptions in `RequestWorker` | Now logged with full traceback |
| Silent network failures in `HTTPClient` | Now logged at ERROR level |
| MCP server lifecycle invisible in logs | Now logged with INFO level |

---

## 2. Residual Tech Debt

### TD-1: No `IMetricsManager` protocol/interface (Low — deferred by design)

**Location:** All consumers of `MetricsManager`.

**Issue:** All constructor parameters are typed as `MetricsManager | None`. There is no abstract
protocol (e.g., `typing.Protocol`) that consumers depend on. This means consumers are coupled to
the concrete class and cannot accept alternative implementations (e.g., a no-op, OpenTelemetry
adapter, or test double) without further changes.

**Impact:** Low. The `None`-guard pattern already provides test isolation. Changing metrics
backends in production would require a refactor.

**Recommendation:** Introduce a `MetricsProtocol(Protocol)` in a future task. Consumers would
type-hint against the protocol, and `MetricsManager` would implicitly satisfy it.

---

### TD-2: `None`-guard pattern repeated at every call site (Low)

**Location:** `tabs_presenter.py`, `request_editor.py`, `response_view.py`, `http_client.py`,
`request_service.py`, `mcp_server_impl.py`.

**Issue:** Each metric tracking call is individually guarded with `if self._metrics:`. This is
explicit and correct but verbose. If the number of tracking call sites grows, the boilerplate
becomes noise.

**Impact:** Cosmetic. No correctness risk.

**Recommendation:** If `TD-1` is addressed with a `MetricsProtocol`, a `NullMetrics` no-op
implementation could replace the `None` guards entirely, simplifying call sites to unconditional
`self._metrics.track_xxx(...)`.

---

### TD-3: `MetricsManager` bundles two unrelated concerns (Medium)

**Location:** `pypost/core/metrics.py`.

**Issue:** `MetricsManager` is responsible for:
1. Prometheus counter definitions and tracking methods.
2. MCP resource exposure (`list_resources`, `read_resource`).
3. Uvicorn server lifecycle (`start_server`, `stop_server`, `restart_server`).

These are three distinct responsibilities in one class. The server-lifecycle and MCP concerns
make `MetricsManager` harder to test in isolation and harder to reason about.

**Impact:** Medium. Injecting `MetricsManager` is correct, but the class itself still violates SRP.

**Recommendation:** Consider a future split:
- `MetricsRegistry` — owns counters and tracking methods (pure, no I/O).
- `MetricsServer` — owns uvicorn thread lifecycle.
- The MCP resource handler could move to `mcp_server_impl.py` or a dedicated adapter.

---

### TD-4: `_extract_mcp_variables` dead-code path in `MCPServerImpl` (Low)

**Location:** `pypost/core/mcp_server_impl.py`, lines 117–147.

**Issue:** The Jinja2 AST variable extraction loop at lines 131–145 runs but produces no output
(the inner body is a bare `pass`). The actual extraction is done below by the regex pattern. The
Jinja2 AST block is dead code and misleads readers about intent.

**Impact:** Low. Cosmetic and confusing.

**Recommendation:** Remove the dead Jinja2 `try/except` block in a cleanup task; keep only the
regex path.

---

### TD-5: `import re` inside method body in `MCPServerImpl` (Low)

**Location:** `pypost/core/mcp_server_impl.py`, line 150.

**Issue:** `import re` is placed inside `_extract_mcp_variables` instead of at module top level.
PEP 8 requires all imports at the top of the file.

**Impact:** Minor style violation; no runtime impact.

**Recommendation:** Move `import re` to the module-level imports section.

---

### TD-6: Trailing whitespace in `pypost/core/http_client.py` (Low)

**Location:** Lines 51, 59 (blank lines with trailing spaces).

**Issue:** CLAUDE.md requires no trailing whitespace. These lines were not introduced by PYPOST-44
but were present before.

**Impact:** Style only.

**Recommendation:** Clean up in next code-quality pass.

---

### TD-7: No unit tests for `MetricsManager` tracking methods (Medium)

**Location:** `tests/` — no `test_metrics.py` exists.

**Issue:** `MetricsManager` itself has no unit tests. Tracking methods, server lifecycle, and the
MCP resource handler are all untested at the unit level. The refactor increases importance of
these tests because `MetricsManager` is now a plain injectable service.

**Impact:** Medium. Counter logic and label names can silently break.

**Recommendation:** Add `tests/test_metrics.py` in a future task covering:
- Counter increments for each `track_*` method.
- `start_server` / `stop_server` lifecycle (mock uvicorn).
- `read_resource` MCP handler returning Prometheus output.

---

## 3. Acceptance Criteria Verification

| AC | Result |
|----|--------|
| `MetricsManager` has no singleton machinery | PASS — `__new__`, `_instance`, `_lock`, `_initialized` all removed |
| `main.py` constructs one instance and passes it to `MainWindow` | PASS |
| All consumers receive `MetricsManager` via constructor | PASS — all 8 affected classes updated |
| No production module outside `main.py` calls `MetricsManager()` | PASS |
| `make test` passes | PASS — 103/103 |
| Tests use mock/fake for `metrics` | PASS — `MagicMock()` injected in all affected test files |

---

## 4. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `metrics=None` silently drops metrics in production | Low | High | `main.py` always passes a live instance; `None` only reachable in tests |
| Thread-safety of `MetricsManager` counters | Low | Medium | Prometheus `Counter` is thread-safe by design |
| SSE duplicate endpoint definitions (`MetricsManager` + `MCPServerImpl`) | Low | Low | Both serve different paths; no conflict detected |
