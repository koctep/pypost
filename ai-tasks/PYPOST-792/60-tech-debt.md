# PYPOST-792: Technical Debt Analysis

## Shortcuts Taken

No intentional "quick fixes" or temporary workarounds were introduced. The fix restores
platform-native tab rendering by removing the offending QSS rule and stop forcing a 48px
close-indicator metric — the correct long-term approach per requirements (no visual redesign).

Minor pragmatic choices (not crutches):

- **QSS guard via regex** (`test_loaded_styles_do_not_customize_tab_geometry`) strips block
  comments then rejects any active `QTabBar::tab` selector. This is stricter than
  "forbid zero-padding only" but matches the architecture decision that *any* box-model
  property on `::tab` disables native rendering. A future task that legitimately needs partial
  tab styling must update both the guard and the architecture note.
- **Synthetic `QTabBar` in geometry tests** rather than driving the real `MainWindow` /
  `RequestEditor` widgets. Sufficient to pin RC1/RC2 but does not exercise the full widget
  tree or macOS native renderer quirks.
- **`set_close_button_size` API retained** as an unused opt-in override. Kept to avoid a
  breaking change and to support deliberate overrides; no production caller uses it after this
  task.

## Code Quality Issues

- **Duplicated style bootstrapping** — `pypost/main.py` installs `PyPostStyle()` at startup,
  then `MainWindow.apply_settings` immediately calls `StyleManager.apply_theme(app,
  settings.theme)`, which re-installs `PyPostStyle()` again for the default `system` theme.
  Both sites must stay in sync manually (palette, close-metric policy). A single composition
  entry point (e.g. `StyleManager.bootstrap(app)` called only from `main.py`, with
  `apply_settings` handling theme/stylesheet reload only) would remove the duplication.
- **Makefile `help` target missing** — `check` was added with a `##` description, but the root
  `Makefile` still lacks the self-documenting `help` target required by the workspace Makefile
  rule. Developers must read the Makefile directly to discover targets.
- **Broad `except Exception` in `StyleManager.load_styles`** — pre-existing; individual file
  read failures are logged and skipped rather than failing fast. Acceptable for resilience but
  can mask a partially loaded stylesheet in production.
- **`environment_variables_widget.py` import reorder** — flake8 E402 fix bundled into this
  task; unrelated to tab layout but harmless.
- **`doc/dev/ui_font_and_styles.md` outdated** — documents font-size pipeline only; does not
  mention `PyPostStyle`, tab close-indicator metrics, or the `QTabBar::tab` prohibition.
  Deferred to Step 7 (Dev Docs).

## Missing Tests

All seven tests in `tests/test_tab_layout_regression.py` declare an explicit timeout via
module-level `pytestmark = pytest.mark.timeout(60)` — **timeout blocker cleared**.

Gaps that remain acceptable for this task but worth follow-up:

| Scenario | Status |
| --- | --- |
| Loaded QSS must not target `QTabBar::tab` | Covered (`test_loaded_styles_do_not_customize_tab_geometry`) |
| Sidebar / editor sub-tab native spacing | Covered (synthetic `QTabBar`, production stylesheet) |
| Default / opt-in close-indicator metrics | Covered |
| `apply_theme("system")` native close metrics | Covered |
| Request tab close button laid out at native size | Covered (`RequestTabHeader` integration) |
| **Dark / light Fusion theme tab layout** | Not covered — geometry tests run with production QSS + `system` theme path; Fusion palette themes use plain Fusion without `PyPostStyle` and were not the reported defect |
| **macOS native renderer / visual regression** | Not automatable in CI — manual verification done in Step 3; offscreen geometry tests proxy but cannot catch icon contrast or segmented-control aesthetics |
| **StyleManager new WARNING/DEBUG logs** | Not covered — low value; observability validated manually in Step 5 |
| **End-to-end `MainWindow` tab regions** | Not covered — would be slow and brittle; synthetic bars deemed sufficient per architecture |

## Performance Concerns

None introduced. `StyleManager.load_styles()` still reads and concatenates all `.qss` files
synchronously on every `apply_styles` call (pre-existing; runs on startup and settings change,
not per frame). `PyPostStyle.pixelMetric` adds a tuple membership check — negligible.
Regression tests use module-scoped fixtures and bounded `processEvents()` — appropriate for
GUI tests with 60s timeout.

## Follow-up Tasks

| Priority | Task | Rationale | Jira |
| --- | --- | --- | --- |
| Medium | **Consolidate style bootstrapping** — single `StyleManager` entry point for initial `PyPostStyle` + theme; remove duplicate install from `main.py` or document why both are required | Duplication noted in roadmap and `20-architecture.md`; drift risk if one site regresses | [PYPOST-793](https://pypost.atlassian.net/browse/PYPOST-793) |
| Medium | **Improve `close.svg` contrast on dark tab chrome** — `#666666` stroke is hard to see at native indicator size on dark tabs; hover (`close-hover.svg`) is fine | Observed during Step 3 manual macOS verification; accessibility / polish | [PYPOST-796](https://pypost.atlassian.net/browse/PYPOST-796) |
| Low | **Add Makefile `help` target** — parse `##` comments for all targets including `check` | Workspace Makefile rule compliance; partially addressed by adding `check` only | [PYPOST-794](https://pypost.atlassian.net/browse/PYPOST-794) |
| Low | **Update `doc/dev/ui_font_and_styles.md`** — document `PyPostStyle`, native-by-default close metrics, and `QTabBar::tab` styling prohibition | Completed in Step 7 | — |
| Low | **Evaluate removing `set_close_button_size`** if no caller materializes — or document explicit override use case in dev docs | API is intentionally kept but currently dead in production | [PYPOST-795](https://pypost.atlassian.net/browse/PYPOST-795) |
| Low | **Pre-existing: replace `print()` in `config_manager.py`** with structured logging | PYPOST-688 / Step 5 observability out-of-scope note | [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) |

## Validation Summary

- `make check` passes (flake8 clean; 1529 tests passed).
- All collected pytest modules have explicit `pytest.mark.timeout` markers (repo-wide scan;
  helper modules under `tests/helpers/` are not collected tests).
- No new technical debt blockers for Step 7.
