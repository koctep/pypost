# Roadmap: PYPOST-621

**Programming Language:** Python (PySide6 / Qt offscreen tests)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `_reload_alert_manager` in `MainWindow`; `TabsPresenter.set_alert_manager`; tests
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Artifacts

| Step | Files |
| --- | --- |
| 1 | `10-requirements.md` |
| 2 | `20-architecture.md` |
| 3 | `main_window.py`, `tabs_presenter.py`, `tests/test_main_window_alert_reload.py` |
| 4 | `40-code-cleanup.md` |
| 5 | `50-observability.md` |
| 6 | `60-tech-debt.md` |
| 7 | `70-dev-docs.md`, `doc/dev/settings_dialog.md` |

## Suggested branch name (reference only)

`feature/PYPOST-621-alert-manager-reload`
