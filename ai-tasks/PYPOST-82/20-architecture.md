# PYPOST-82 Architecture: Document Autonomous-Default Pattern

## Overview

Documentation-only change. No new modules, constructors, or runtime paths.

---

## Target Artifacts

| Artifact | Change |
| --- | --- |
| `pypost/core/template_service.py` | Add class docstring on `TemplateService` |
| `doc/dev/template_service.md` | Add cross-reference to class docstring under Injection section |

---

## Docstring Content (required sections)

1. **Role** — central `{{...}}` substitution entry point.
2. **Autonomous-default** — optional `template_service` param; `None` → local
   `TemplateService()` per consumer (PYPOST-45).
3. **Production** — single instance from `main.py`, propagated through UI/MCP chain.
4. **Independent construction** — separate `jinja2.Environment` per autonomous default;
   intentional, low cost.
5. **Pointer** — `doc/dev/template_service.md` for consumer matrix and tests.

---

## Out of Scope

- Modifying `HTTPClient`, `RequestService`, or `MCPServerImpl` constructors.
- New tests (docstring presence is verified by review, not a dedicated test).
- Observability changes.

---

## Verification

- `make test` — full suite green (no code-path changes expected).
- Manual review: class docstring readable in IDE hover and `help(TemplateService)`.
