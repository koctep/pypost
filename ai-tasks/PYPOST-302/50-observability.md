# PYPOST-302: Observability

## Scope

Refactor only — no new user-facing actions or metrics.

## Logging

- Unchanged: `TabsPresenter.handle_new_tab` continues to log
  `new_tab_action_triggered source=<source> tabs_before=<count>`.
- Plus-tab clicks still route through `handle_new_tab("plus_button")` via
  `RequestTabHeader.new_tab_requested`.

## Metrics

- Unchanged: `MetricsManager.track_gui_new_tab_action(source)` called from presenter.
- Sources remain `plus_button`, `shortcut`, `unknown`.

## Rationale

Observability stays at the presenter boundary where business context (tab counts, metrics) lives.
The header emits a UI signal only; no duplicate logging added in the component.
