# PYPOST-490: Technical Debt Analysis

## Review Summary

**Verdict:** Requirements met. Test-only deliverable; no production wiring defects found.

The implementation in `tests/test_settings_hidden_toggle_logging_e2e.py` matches the
architecture plan and Definition of Done from `10-requirements.md`:

| Requirement | Status | Evidence |
| --- | --- | --- |
| Full journey: Settings → apply → env manager → toggle log | Met | `_run_settings_to_toggle_chain` exercises `SettingsDialog.accept()`, real `MainWindow.apply_settings`, `EnvPresenter._open_env_manager`, and toggle under patched `EnvironmentDialog.exec` |
| Default policy: key name not readable | Met | `test_default_masked_toggle_log_after_settings_apply` asserts `key=********` and no `API_KEY` in caplog |
| Opt-in policy: key name readable | Met | `test_readable_toggle_log_when_settings_opt_in` asserts `key=API_KEY` |
| `env_name` and `hidden` in both modes | Met | Both tests match log fragment including `env_name=Dev` and `hidden=True` |
| Variable values never logged | Met | `_assert_no_value_leak` in both tests |
| Traceable to PYPOST-448 debt | Met | Module docstring, file name, and journey comments reference PYPOST-448 / PYPOST-490 |
| No product behavior change | Met | No `pypost/**` production changes |

Validation re-run at review: 2/2 tests pass (`pytest tests/test_settings_hidden_toggle_logging_e2e.py`).

**PYPOST-448 debt closure:** This task resolves the High-priority missing-test item from
[PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md) — *"No end-to-end
test covers Settings save → MainWindow.apply_settings → EnvPresenter._open_env_manager →
masked toggle log."* Close [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) and
mark that PYPOST-448 follow-up as done when this task ships.

## Shortcuts Taken

- **Presenter-centric integration, not full UI automation.** Settings and environment manager
  modals are driven via `accept()`, real method calls, and patched `EnvironmentDialog.exec`
  rather than click-through automation. Matches approved architecture; the regression risk is
  wiring, not widget event delivery.
- **Settings path skips disk persistence.** Tests call `SettingsDialog.accept()` +
  `MainWindow.apply_settings()` directly instead of `MainWindow.open_settings()`. Persistence
  of `log_hidden_key_names` remains covered by `test_settings_persistence.py` (per
  architecture Q&A).
- **Thin MainWindow shell.** Heavy dependencies are patched during `MainWindow.__init__`, mirroring
  `tests/test_apply_settings_font.py`. Real `apply_settings` runs after injecting a real
  `EnvPresenter`.

## Code Quality Issues

- `_make_integration_window` duplicates the MainWindow partial-construction patch list from
  `tests/test_apply_settings_font.py`. Acceptable for a focused test module; a shared test
  helper would reduce drift if more integration tests adopt this pattern. No existing Jira ticket.
- `HiddenToggleLogPolicy` still imports `HIDDEN_MASK` from the UI layer (core → UI dependency).
  Pre-existing from PYPOST-448; not introduced by this task.
  - Jira: [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491) (Medium, Debt)

## Missing Tests

- **Optional negative guard** (architecture low priority): call `_open_env_manager` before
  `apply_settings` with opt-in settings prepared but not applied — expect masked log. Would
  clarify policy is read at dialog construction time without duplicating unit coverage. Not
  required for DoD; defer unless maintainers want extra regression signal.
- **Policy change while environment manager is open** — explicitly out of scope (PYPOST-448
  accepted UX limitation).
- **Persistence round-trip with default masked toggle logging** — separate scope.
  - Jira: [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489) (Low, Debt)
- **Settings UI discoverability** (security/logging section grouping) — separate scope.
  - Jira: [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492) (Low, Debt)

No new missing-test gaps introduced by PYPOST-490 beyond the optional guard above.

## Performance Concerns

None. Two fast Qt integration tests with fakes; no new runtime paths.

## Deviations from Architecture

None. Implementation follows `20-architecture.md`: two acceptance tests, reused presenter
fakes, patched `exec`, caplog at INFO, constants aligned with existing env-dialog tests.

## Follow-up Tasks

Remaining PYPOST-448 debt items (link existing tickets; do not duplicate):

| Priority | Ticket | Description |
| --- | --- | --- |
| High | [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) | **This task** — integration test for settings → apply → env dialog → toggle log. **Closes PYPOST-448 missing-test debt.** |
| High | [PYPOST-488](https://pypost.atlassian.net/browse/PYPOST-488) | Document `log_hidden_key_names` in dev docs (may already be resolved in PYPOST-448 STEP 7). |
| Medium | [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491) | Extract `HIDDEN_MASK` to shared constants module. |
| Low | [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492) | Group security/logging settings in SettingsDialog. |
| Low | [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489) | Extend env persistence e2e for default masked toggle logging. |

No new Jira tickets recommended for PYPOST-490 scope.
