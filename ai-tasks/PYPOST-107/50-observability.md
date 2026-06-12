# PYPOST-107: Observability

No new log lines required. Font propagation for body editors uses existing
`apply_settings` flow (`MainWindow` → global QSS → inherited `FontChange` on editors).

Existing `settings_applied font_size=%d` in `MainWindow.apply_settings` remains sufficient.
