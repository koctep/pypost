# PYPOST-82: Developer Documentation

## What Changed

Added a class-level docstring on `TemplateService` documenting the autonomous-default pattern
(PYPOST-45). Updated `doc/dev/template_service.md` to point readers to the in-code reference.

---

## Files Modified

| File | Change |
| --- | --- |
| `pypost/core/template_service.py` | Class docstring: autonomous-default, production injection, trade-off |
| `doc/dev/template_service.md` | Cross-reference under Injection section |

---

## Reading Order

1. `help(TemplateService)` or IDE hover on the class — canonical summary.
2. `doc/dev/template_service.md` — consumer matrix, lifecycle, troubleshooting.
