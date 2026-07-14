# PYPOST-798: Observability

## Production observability

No changes. The fallback path routes through the same signals and presenter handler as the
primary path:

1. `_on_tab_bar_clicked` → `new_tab_requested`
2. `TabsPresenter.handle_new_tab("plus_button")`
3. INFO log `new_tab_action_triggered source=plus_button tabs_before=<count>`
4. Metric `gui_new_tab_actions_total{source=plus_button}`

## Test observability

Tests assert behavioral outcomes (signal emission, request tab count) — no log/metric
assertions required for this belt-and-suspenders path. Presenter metrics are exercised
indirectly when `handle_new_tab` runs; dedicated metric assertions are out of scope for
this debt follow-up.
