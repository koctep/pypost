# PYPOST-425: Dev Docs

## Updates

- `doc/dev/ui_font_and_styles.md` — linked PYPOST-425; noted `EnvPresenter` loop removal.
- `doc/dev/environments_dialog.md` — `apply_settings` no longer documents `apply_font`.

## Verification

Docs match implementation: font propagation is global QSS + `QApplication.setFont` only.
