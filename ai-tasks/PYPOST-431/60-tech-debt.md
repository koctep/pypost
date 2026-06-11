# Tech Debt Review: PYPOST-431 — globalPosition() migration

**Ticket**: PYPOST-431
**Date**: 2026-06-11
**Verdict**: SAFE TO CLOSE

---

## 1. Summary

Two-line API migration removes Qt 6 deprecation warnings from variable-hover
tooltip positioning.  No new debt introduced.

---

## 2. Strengths

| Strength | Detail |
|----------|--------|
| Minimal surface | Two call sites, one-line each |
| Behaviour parity | Tooltip text and show/hide logic unchanged |
| Test coverage | Existing `test_variable_hover.py` suite validates contracts |

---

## 3. Tech Debt Items (Follow-Up)

### TD-1 (INFO) — Mixin type hints

**Description**: `VariableHoverMixin` uses `object` base with `type: ignore` on
`super().mouseMoveEvent` — pre-existing.

**Tracking**: [PYPOST-250](https://pypost.atlassian.net/browse/PYPOST-250)

---

## 4. Blocker Review

No blockers.  Acceptance criteria met.
