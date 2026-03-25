# PYPOST-404 — Tech Debt Review

**Date**: 2026-03-25
**Author**: team_lead
**Jira**: PYPOST-404

---

## 1. Summary

The PYPOST-404 fix is surgical and well-scoped. Two logical changes were made:

1. Reorder `apply_settings` so `app.setFont(font)` executes after `style_manager.apply_styles(app)`,
   preventing Qt's stylesheet re-polish from overriding the user-configured font size.
2. Inject the `ConfigManager` instance from `main.py` into `MainWindow`, eliminating a redundant
   `load_config()` call on startup.

The implementation matches the architecture exactly. No new abstractions, no new dependencies, no
regressions (191 passed, 0 failed).

---

## 2. Tech Debt Identified

### TD-1 — Explicit widget font loop is now belt-and-suspenders only (Low severity)

**Location**: `pypost/ui/main_window.py` — `apply_settings`, lines ~163-170

**Description**: The loop that explicitly calls `w.setFont(font)` on a hardcoded list of widgets
was originally the only mechanism preventing partially-correct behaviour after the stylesheet reset.
After the fix, `app.setFont(font)` is called last and propagates the font application-wide. The
explicit loop is now redundant for the named widgets; they already inherit the correct font via
`app.setFont`.

**Risk**: Low. The loop is harmless. It provides an extra guarantee for the enumerated widgets and
does not conflict with the app-wide font. However, the list will silently drift out of date as new
widgets are added, creating a false sense of explicit coverage.

**Recommendation**: Leave in place for this release. Consider removing it in a dedicated clean-up
task once the team confirms that app-wide font inheritance is sufficient for all current and planned
widgets.

---

### TD-2 — `apply_settings` accepts `settings` as a plain positional argument (Low severity)

**Location**: `pypost/ui/main_window.py` — `def apply_settings(self, settings) -> None`

**Description**: The parameter type is not annotated; `settings` is typed as `Any` implicitly.
`AppSettings` is the only type ever passed, but the lack of annotation reduces static-analysis
coverage and IDE support.

**Risk**: Low. No bug vector. Maintenance friction only.

**Recommendation**: Add `settings: AppSettings` annotation in a future clean-up pass.

---

### TD-3 — `main.py` creates `ConfigManager` before knowing it will be consumed (Very low severity)

**Location**: `pypost/main.py` — `main()`

**Description**: `main.py` creates `ConfigManager()` and calls `load_config()` to get `settings`
for `MetricsManager`. `MainWindow` now also receives the same `config_manager`. This is correct and
efficient. However, if `MetricsManager` is ever refactored to not need a pre-loaded `AppSettings`,
the early `load_config()` call in `main.py` would become the sole reason `ConfigManager` exists
there — which could confuse future readers.

**Risk**: Very low. The current flow is correct and clearly intentional.

**Recommendation**: No action needed now. Worth noting in architecture docs so future refactors
preserve the single-load guarantee.

---

## 3. No Tech Debt Introduced

The following were explicitly evaluated and found to introduce no new debt:

| Area | Verdict |
|------|---------|
| Test isolation strategy (mock patches in `_make_window`) | Appropriate. Each test rebuilds the window, avoids shared mutable state. |
| Module-scoped `qapp` fixture | Correct Qt constraint; `QApplication` is a singleton per process. |
| Optional `config_manager` parameter defaulting to `None` | Clean backward-compatible signature. |
| Two `logger.debug` calls added to `apply_settings` and `__init__` | Targeted; DEBUG level; no noise in default log output. |

---

## 4. Overall Assessment

The fix is production-ready. The three tech debt items identified are pre-existing (TD-2, TD-3) or
accepted trade-offs (TD-1). None require immediate action. The codebase is in a better state after
this change than before: duplicate config loading is eliminated, a silent startup bug is fixed, and
the call-order contract is now validated by automated tests.
