# PYPOST-598: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE — D1 SRP split delivered; public API and form row order preserved;
69 settings tests pass; no blockers.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Split settings domains | Met | Eight section modules under `pypost/ui/widgets/settings/` |
| Thin coordinator facade | Met | `settings_dialog.py` ~185 LOC |
| Same UX / validation / save behavior | Met | Tests unchanged; form order interleaving preserved |
| Widget attrs on `dlg` for tests | Met | Mirrored in coordinator `__init__` |
| Logging / patch paths preserved | Met | `50-observability.md` |

## Shortcuts Taken

- Section builders lazy-import `show_invalid_*` from `settings_dialog` to preserve test patch
  targets — creates a mild circular import that resolves at runtime (acceptable for facade
  pattern; optional future cleanup: move patch targets to a dedicated `settings_dialog_ui.py`).
- `EncryptionMigrationSection` receives confirm/result callables via constructor rather than
  importing `collection_item_dialogs` directly (keeps patch surface on dialog module).
- No new per-section unit tests; existing `SettingsDialog` Qt tests provide regression coverage.

## Code Quality Issues

None blocking.

| ID | Issue | Severity | Tracking |
| --- | --- | --- | --- |
| D3 | Duplicated encryption form-state between `accept()` and migration handlers | Medium | [PYPOST-600](https://pypost.atlassian.net/browse/PYPOST-600) |
| D5 | `EncryptionMigrationService` constructed inside dialog when storage provided | Low | [PYPOST-602](https://pypost.atlassian.net/browse/PYPOST-602) |

## Missing Tests

Optional (non-blocker): direct unit tests for individual section classes if domains diverge
further. Current dialog-level tests cover layout order, validation, migration, and e2e paths.

## Performance Concerns

None. Modal dialog; refactor is maintainability-only.

## Follow-up Tasks

No new Jira tickets created. Remaining debt already tracked:

- [PYPOST-600](https://pypost.atlassian.net/browse/PYPOST-600) — unify encryption form builder
- [PYPOST-602](https://pypost.atlassian.net/browse/PYPOST-602) — inject migration service at call site

## Blocker Verdict

**SAFE TO CLOSE**
