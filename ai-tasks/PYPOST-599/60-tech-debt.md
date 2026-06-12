# PYPOST-599: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE — D2 addressed; `HotkeysDialog` derives rows from tagged `QAction`
metadata; shortcut behavior preserved; tests added.

| Requirement | Status | Evidence |
| --- | --- | --- |
| No hardcoded shortcut table | Met | `hotkeys_dialog.py` uses `collect_hotkey_rows` |
| Derive from app actions | Met | `register_hotkey` / `tag_action` on `QAction` |
| Preserve UX labels / groupings | Met | Section order + `pypost_hotkey_label` overrides |
| Behavior unchanged | Met | 74 targeted tests pass |
| Automated coverage | Met | `tests/test_hotkeys.py` (5 tests) |

## Shortcuts Taken

- Contextual shortcuts (F2 environment rename, Ctrl+F response search, history copy) are not
  registered with the hotkey helpers — help dialog scope matches pre-task global shortcuts only.
- `register_hotkey_group` uses a display-only `QAction` without `triggered` slot for Alt+1..9.
- Native key text formatting (`QKeySequence.NativeText`) may differ slightly by platform in the
  Shortcut column; bindings unchanged.

## Code Quality Issues

None blocking.

| ID | Issue | Severity | Tracking |
| --- | --- | --- | --- |
| — | Localization of menu/help strings | Low | Existing PYPOST-11 item #1 |
| — | Register remaining contextual shortcuts in help | Low | Optional future enhancement |

## Missing Tests

Optional (non-blocker): end-to-end test opening Help → Hotkeys on a fully constructed
`MainWindow` (heavy Qt setup). Unit tests cover collection and dialog population.

## Performance Concerns

None. Dialog opened infrequently; collection is O(n) over `QAction` children.

## Follow-up Tasks

No new Jira tickets required. Remaining PYPOST-374 dialog debt already tracked:

- [PYPOST-600](https://pypost.atlassian.net/browse/PYPOST-600) — encryption form duplication
- [PYPOST-601](https://pypost.atlassian.net/browse/PYPOST-601) — About version metadata
- [PYPOST-602](https://pypost.atlassian.net/browse/PYPOST-602) — migration service injection

## Blocker Verdict

**SAFE TO CLOSE**
