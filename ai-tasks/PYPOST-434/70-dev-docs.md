# Developer Documentation: PYPOST-434 — pytest import path

**Ticket**: PYPOST-434
**Author**: Team Lead
**Date**: 2026-03-26

---

## 1. Overview

This ticket fixed CI and local runs where `pytest` could not import the `pypost` package
because the repository root was not on `sys.path`.  The fix is documented in developer
docs so new contributors do not rely on a manual `PYTHONPATH`.

---

## 2. Documentation Updated

| File | Change |
|------|--------|
| `doc/dev/setup.md` | Added *Unit tests (pytest)*: commands, pythonpath note, CI pointer. |

---

## 3. What Was Not Added

- No new top-level doc in `doc/dev/README.md` (setup guide remains the entry point).
- No change to [testing.md](../../doc/dev/testing.md): MCP and Prometheus only, not pytest
  unit tests.

---

## 4. Maintainer Notes

- If the project later adds `pyproject.toml` with an installable package, revisit whether
  `pythonpath` remains the preferred approach vs editable installs.
- Tech debt follow-ups: `doc/dev/tech-debt/PYPOST-434.md`.
