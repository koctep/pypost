# PYPOST-425: Code Cleanup

## Removed

- `EnvPresenter.apply_font` method and `QFont` / `QApplication` imports used only for it.
- `test_apply_font_sets_font_on_env_bar_widgets` — tested removed API.
- Stale `settings_btn` mock in `test_apply_settings_font._make_window`.

## Verified unchanged

- `MainWindow.apply_settings` — no widget loop (PYPOST-106).
- `TabsPresenter.apply_settings` — indent/JSON colors only; no font loop.

## Result

No dead font-propagation paths in main window or env presenter.
