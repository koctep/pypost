# PYPOST-1214: Technical Debt Analysis

## Shortcuts Taken

- The mitigation bounds process lifetime rather than proving or repairing an upstream
  Qt/PySide allocation defect.

## Code Quality Issues

- The GUI module keyword inventory in the diagnostic harness is intentionally curated and
  can drift as new GUI tests are added.

## Missing Tests

- The native crash path cannot be asserted deterministically as a normal in-process test;
  the full mode remains a diagnostic procedure.

## Performance Concerns

- Bounded subprocesses add startup overhead and may increase total wall-clock time.

## Follow-up Tasks

- NON-BLOCKER — pre-existing: `tests/test_main_window_alert_reload.py` can still
  reproduce the PYPOST-1117 native `StyleManager.apply_theme` SIGSEGV when run in the
  normal parallel suite; the parent epic owns continued diagnosis.
- NON-BLOCKER — revisit the GUI module discovery policy if new GUI test families are not
  covered by the harness inventory.
- NON-BLOCKER — reassess the batch-size default after PySide6 or Qt upgrades.
