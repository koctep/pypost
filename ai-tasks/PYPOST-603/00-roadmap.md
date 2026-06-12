# Roadmap: PYPOST-603

## Programming Language

Python 3.10+ (PyPost project standard).

## Step Status

- [x] **STEP 3: Development**
  - [x] `AppSettings.theme` (`system` | `light` | `dark`)
  - [x] Theme combo in editor settings section
  - [x] `StyleManager.apply_theme` + `MainWindow.apply_settings`
  - [x] `resolve_json_syntax_colors` / `TabsPresenter` theme wiring
  - [x] Tests
- [ ] **STEP 6: Review and Technical Debt** — `60-tech-debt.md`

## Scope Notes

- Theme only; custom JSON syntax colors deferred to PYPOST-604 (duplicate scope).

## Suggested branch

`feature/PYPOST-603-app-theme-settings`
