# PYPOST-695: Technical Debt

## Blockers

None — safe to close.

## Follow-ups (non-blocker)

- **StyleManager in composition root** — still constructed inside `MainWindow`; tracked under
  PYPOST-43 presenter extraction.
- **Presenter extraction** — `CollectionsPresenter`, `TabsPresenter`, `EnvPresenter` remain
  internal to `MainWindow` ([PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43)).
