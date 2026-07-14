# PYPOST-793: Developer Documentation

## Summary

Documented `StyleManager.apply_appearance` as the single production entry point for theme, global
QSS, and application default font. Removed the stale note that `main.py` installs `PyPostStyle`
before the main window is shown.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_font_and_styles.md` | Overview, pipeline diagram, API, troubleshooting, and Related updated for PYPOST-793 |

## Documentation Highlights

### Single entry point

Production callers use `StyleManager.apply_appearance(app, theme=..., font_size=...)`. The method
runs `apply_theme` → `apply_styles` → `app.setFont` in a fixed order (PYPOST-404 call-order
fix is encapsulated here).

### Call sites (unchanged behavior)

- `MainWindow.__init__` → `apply_settings` → `apply_appearance`
- `MainWindow.showEvent` → deferred `apply_settings` → `apply_appearance`
- `MainWindow.open_settings` → save → `apply_settings` → `apply_appearance`

### Low-level APIs

`apply_theme`, `apply_styles`, and `load_styles` remain documented as building blocks for unit
tests and internal use — not for production wiring.

### Observability

DEBUG logs `apply_appearance_start` and `apply_appearance_font_applied` live on
`StyleManager.apply_appearance` (see `ai-tasks/PYPOST-793/50-observability.md`).

## Verification

- Doc matches `pypost/ui/styles/style_manager.py` and `pypost/ui/main_window.py`.
- Pipeline order covered by `tests/test_style_manager_appearance.py`.
- Delegation covered by `tests/test_apply_settings_font.py`.

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: (subagent)
