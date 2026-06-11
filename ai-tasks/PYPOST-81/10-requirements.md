# PYPOST-81: Logger placement in mcp_server_impl

**Issue type:** Tech Debt
**Priority:** Medium
**Source:** `ai-tasks/PYPOST-45/60-review.md` (TD-2)
**Date:** 2026-06-12

---

## 1. Background

`pypost/core/mcp_server_impl.py` previously declared `logger = logging.getLogger(__name__)`
between third-party import blocks (after `from starlette.applications import Starlette` and
before remaining `starlette` / `mcp` imports). PEP 8 and project style require module-level
assignments after all imports.

---

## 2. Functional Requirements

### FR-1 — Logger after imports

`logger = logging.getLogger(__name__)` must appear only after the final import statement in
`mcp_server_impl.py`.

### FR-2 — No behaviour change

Moving the logger must not alter runtime behaviour, logging configuration, or import order
side effects.

---

## 3. Out of Scope

- Reordering or consolidating import groups beyond what is needed for FR-1.
- Other style debt from PYPOST-45 (e.g. trailing whitespace in `http_client.py`).

---

## 4. Acceptance Criteria

- [x] `logger` assignment is the first module-level statement after all imports.
- [x] Import blocks remain grouped (stdlib → third-party → local).
- [x] Full pytest suite passes.
- [x] `flake8` clean on `mcp_server_impl.py`.

---

## 5. Product Owner Review

**Outcome:** Approved. Style-only debt; no user-facing behaviour change.
