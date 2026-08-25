# PYPOST-1145: Technical Debt Analysis

**Verdict:** `SettingsDialog` now uses a five-tab `QTabWidget` grouped by user-guide
categories. Section builders and `accept()` semantics are unchanged. Layout contract tests
and updated settings suites pass.

**SAFE TO CLOSE** after commit. Follow-up items below are non-blocking enhancements.

Scope reviewed:
- `pypost/ui/dialogs/settings_dialog.py`
- `pypost/ui/widget_ids.py` (`SETTINGS_TABS`)
- `tests/test_settings_dialog_tabbed_layout.py` (6 tests)
- Updated layout accessors in existing settings test modules

---

## Shortcuts Taken

1. **Fixed tab order hard-coded in tuple:**
   - `SETTINGS_TAB_LABELS` is a module-level tuple; reordering tabs requires code change.
   - *Improvement:* Optional settings metadata registry driving tab labels and section assignment.

2. **No scroll areas inside tall tabs:**
   - Encryption and Network tabs may still grow tall on small displays.
   - *Improvement:* `QScrollArea` per tab page if vertical overflow becomes an issue.

---

## Code Quality Issues

None blocking. Coordinator remains ~200 LOC; section SRP from PYPOST-598 preserved.

---

## Missing Tests

1. **Tab widget identity spot-check:**
   - `SETTINGS_TABS` is asserted in tabbed layout tests but not in `test_ui_identity_spotcheck.py`.
   - *Improvement:* Add settings dialog open + `findChild(QTabWidget, SETTINGS_TABS)` spot-check.

2. **Agent dialog settle with tabs:**
   - `agent_dialog_settle` exercises nested layouts; tab chrome adds another layer.
   - *Improvement:* Extend teardown stress coverage if forced-GC regressions appear.

---

## Performance Concerns

None — layout change only; no additional widgets beyond five tab page containers.

---

## Follow-up Tasks

| Priority | Item | Notes |
| --- | --- | --- |
| Low | `QScrollArea` per tab when content exceeds viewport | UX polish |
| Low | `SETTINGS_TABS` in `test_ui_identity_spotcheck.py` | Agent identity coverage |
| Low | Side navigation if tab count exceeds ~6 categories | Alternative to more tabs |

No new Jira tickets created — items are minor polish.
