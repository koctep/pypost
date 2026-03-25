# Tech Debt Review — PYPOST-83: Fix Fragile Positional call_args in test_request_service

**Author:** Team Lead
**Date:** 2026-03-25
**Status:** Complete

---

## 1. Summary

PYPOST-83 resolves a targeted piece of tech debt introduced during the PYPOST-43–51
refactoring cycle. The fix converts positional `send_request` call arguments to keyword
arguments and replaces three fragile numeric-index mock assertions with named-key lookups.
The change is minimal (two files, six lines net) and carries no functional risk.

---

## 2. Tech Debt Items Closed

### TD-1 — Fragile positional call-site in `request_service.py`

- **Before:** `send_request(request, variables, stream_callback, stop_flag, headers_callback)`
- **After:** `send_request(request, variables=variables, stream_callback=stream_callback, ...)`
- **Risk eliminated:** Any future reordering or insertion of parameters into
  `HTTPClient.send_request` would have silently passed wrong values at runtime. That risk
  is now gone — the call site binds every argument by name.

### TD-2 — Positional-index mock assertions in `test_request_service.py`

- **Before:** `call_args[0][1]`, `call_args[0][2]`, `call_args[0][4]`
- **After:** `call_args.kwargs["variables"]`, `call_args.kwargs["stream_callback"]`,
  `call_args.kwargs["headers_callback"]`
- **Risk eliminated:** Index-based assertions would silently compare the wrong value or
  raise `IndexError` after a parameter reorder. Named lookups are immune to positional
  layout changes.

---

## 3. Remaining Tech Debt

None introduced or discovered by this task. The two changes are internally consistent and
the observability review (Step 6) confirmed no coverage gaps.

---

## 4. Code Quality Assessment

| Criterion | Assessment |
|---|---|
| Scope discipline | Excellent — exactly the four lines specified; no unrelated edits |
| Correctness | Verified — 23 tests pass, all acceptance criteria met |
| Readability | Improved — keyword arguments are self-documenting at the call site |
| Test robustness | Improved — `.kwargs["name"]` assertions are stable under refactoring |
| Style compliance | Pass — line length ≤ 100 chars, LF endings, UTF-8, no trailing whitespace |
| Coverage | Unchanged — threshold (50 %) maintained |

---

## 5. Architecture Compliance

The implementation matches the architecture document (`20-architecture.md`) exactly:

- Step A (keyword args in `request_service.py`): implemented at lines 129–135.
- Step B (`.kwargs` assertions in `test_request_service.py`): implemented at lines 36, 44, 52.
- Co-dependency (Steps A and B must land together): satisfied in a single commit.

---

## 6. Verdict

No residual tech debt. The refactor is clean, minimal, and production-ready.
