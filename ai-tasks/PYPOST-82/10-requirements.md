# PYPOST-82: Document TemplateService Autonomous-Default Pattern

**Issue type:** Tech Debt
**Priority:** Medium
**Source:** ai-tasks/PYPOST-45/60-review.md (TD-3)
**Date:** 2026-06-12

---

## Goals

PYPOST-45 removed the module-level `template_service` singleton and introduced constructor
injection with per-class defaults. Future maintainers may expect a shared Jinja2 `Environment`
across independently constructed consumers. The autonomous-default trade-off must be documented
at the source so readers do not misinterpret separate instances as a bug.

---

## User Stories

- As a **core developer**, I want the `TemplateService` class docstring to explain when
  consumers create their own instance vs. receive an injected one, so I can wire tests and
  new call sites correctly.
- As a **reviewer**, I want a single authoritative in-code reference to the pattern, so I
  do not need to hunt through architecture artifacts from PYPOST-45.

---

## Definition of Done

1. `TemplateService` has a class-level docstring describing the autonomous-default pattern.
2. The docstring covers production injection from `main.py`, isolated test construction, and
   the separate-`Environment` trade-off.
3. `doc/dev/template_service.md` cross-references the class docstring (Step 7).
4. No runtime behaviour changes; existing tests pass.

---

## Task Description

TD-3 in the PYPOST-45 review recommended documenting the autonomous-default pattern in the
`TemplateService` class docstring. `doc/dev/template_service.md` already describes injection
at a high level; this task closes the gap by anchoring the pattern on the class itself.

**Out of scope:** changing constructor signatures, removing autonomous defaults, or adding
new metrics/logging.

---

## Q&A

| Question | Answer |
| --- | --- |
| Why document on the class, not only in `doc/dev/`? | Developers land on `template_service.py` first; the class docstring is the canonical API surface. |
| Does this change behaviour? | No — documentation only. |
