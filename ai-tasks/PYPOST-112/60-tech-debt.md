# PYPOST-112: Technical Debt Analysis

## Resolved

- **Font inheritance / manual `apply_settings` propagation (PYPOST-12)**: Root causes documented;
  solution delivered by PYPOST-106 (global QSS + `app.setFont`, no widget loop) and PYPOST-107
  (`CodeEditor` font metric refresh). `MainWindow.apply_settings` is clean and maintainable.

## Shortcuts Taken

- None for this task.

## Follow-up Tasks

- Optional audit of hardcoded `font-size` in widget-level QSS (from PYPOST-106) — UX polish,
  not a blocker. No new Jira issue created; tracked under PYPOST-106 debt notes.

## Verdict

**SAFE TO CLOSE** — no blockers.
