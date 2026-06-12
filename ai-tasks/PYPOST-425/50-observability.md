# PYPOST-425: Observability

## Impact

No new log lines. Existing `apply_settings_start` / `apply_settings_font_applied` debug logs in
`MainWindow.apply_settings` remain the font observability contract.

## Verification

Font size still visible via:

- `apply_settings_font_applied point_size=%d` after `app.setFont`
- User-visible Settings font change across main window

No observability regression.
