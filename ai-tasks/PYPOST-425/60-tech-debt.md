# PYPOST-425: Technical Debt

## Resolved

- **TD-1 (PYPOST-404)**: Redundant explicit widget font loops removed from env presenter;
  main-window loop was already removed in PYPOST-106.

## Remaining (non-blockers)

- **Widget-level fixed `font-size` in QSS** (hotkeys, about, validation labels): optional UX
  audit for very large user font sizes — same as PYPOST-106 follow-up.
- **`apply_settings(settings)` untyped in MainWindow**: tracked as
  [PYPOST-426](https://pypost.atlassian.net/browse/PYPOST-426).

## Verdict

**SAFE TO CLOSE** — no blockers.
