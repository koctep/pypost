# PYPOST-404 Roadmap — [Bug] Font size settings not applied on application startup

**Type**: Bug
**Priority**: High
**Labels**: —
**Status**: Done

## Summary

After the user changes font size settings and restarts the application, the selected font size
is not applied. The application should persist and restore font size preferences on startup.

**Steps to reproduce:**
1. Change font size settings in the application.
2. Restart the application.
3. Verify font size after launch.

**Actual result:** Font size setting is not applied after restart.
**Expected result:** Application applies and saves the selected font size setting on startup.

---

## Milestones

| # | Phase                  | Deliverable               | Status         |
|---|------------------------|---------------------------|----------------|
| 0 | Kickoff                | Roadmap initialized       | ✅ Done        |
| 1 | Requirements           | 10-requirements.md        | ✅ Done        |
| 2 | Product Owner Review   | Requirements approved     | ✅ Done        |
| 3 | Architecture           | 20-architecture.md        | ✅ Done        |
| 4 | Team Lead Review       | Architecture approved     | ✅ Done        |
| 5 | Implementation         | Code changes + cleanup    | ✅ Done        |
| 6 | Observability          | 50-observability.md       | ✅ Done        |
| 7 | Review & Docs          | 60-review.md, 70-dev-docs | ✅ Done        |
| 8 | Commit & Close         | Final commit + Jira close | ✅ Done        |

---

## Project Manager Update

**Date**: 2026-03-25
**Phase**: Observability Complete — Review & Docs phase now active (Phase 7).

### Completed Milestones
- Phase 0 — Roadmap created; Jira PYPOST-404 transitioned to In Progress.
- Phase 1 — Requirements gathered; root cause identified in `10-requirements.md`.
  - Root cause: `apply_settings` calls `app.setFont(font)` before `style_manager.apply_styles(app)`.
    Qt 6 `setStyleSheet()` re-polishes all widgets and resets the app-level font, overriding the
    configured font size.
- Phase 2 — Product Owner review complete; requirements approved.
- Phase 3 — Architecture designed by `senior_engineer` in `20-architecture.md`.
  - Fix: move `style_manager.apply_styles(app)` before `app.setFont(font)` in `apply_settings`.
  - FR-4: inject `ConfigManager` from `main.py` into `MainWindow` to eliminate duplicate load.
  - Test plan: `tests/test_apply_settings_font.py` with T-1, T-2, T-3.
- Phase 4 — Team Lead architecture review complete; approved.
- Phase 5 — Implementation and code cleanup complete (`40-code-cleanup.md`).
  - All three required changes applied: `apply_settings` reorder, FR-4 injection, new test file.
  - Full test suite: **191 passed, 0 failed**. No regressions.
- Phase 6 — Observability complete (`50-observability.md`).
  - Two `logger.debug` calls added to `pypost/ui/main_window.py`:
    1. `apply_settings_start` / `apply_settings_font_applied` — captures requested vs. applied
       font size; divergence in logs signals a regression.
    2. `config_manager_source` — confirms FR-4 injection is active at runtime.
  - No metrics additions required; fix is a synchronous call-order correction.

### Active Risks / Blockers
- None blocking. All code changes, tests, and observability are in place.
- `60-review.md` and `70-dev-docs.md` not yet produced — hand-off needed to `team_lead`.

### Next Action
- Hand off to `team_lead` to produce `60-review.md` and `70-dev-docs.md`, then perform final
  commit (Phases 7–8).
- `project_manager` to close Jira PYPOST-404 after Phase 8 completes.
