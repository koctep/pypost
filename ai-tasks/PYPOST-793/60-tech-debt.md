# PYPOST-793: Technical Debt Analysis

## Shortcuts Taken

No intentional "quick fixes" or temporary workarounds were introduced. The consolidation adds
`StyleManager.apply_appearance` as a facade over the existing `apply_theme` → `apply_styles` →
`setFont` sequence — the correct long-term ownership model per R-P3-004.

Minor pragmatic choices (not crutches):

- **`MainWindow` remains the caller** for initial appearance (via `apply_settings` in
  `__init__` and `showEvent`) rather than invoking `apply_appearance` from `main.py`. Matches
  architecture decision: settings load through `StateManager` inside `MainWindow`; composition-root
  injection refactor is explicitly out of scope.
- **`test_apply_settings_font.py` now asserts delegation** to `apply_appearance` rather than
  exercising the full font pipeline through `MainWindow`. Pipeline parity tests live in
  `test_style_manager_appearance.py` — acceptable split; avoids duplicating heavy mocks.

## Code Quality Issues

- **`doc/dev/ui_font_and_styles.md` outdated** — still describes the pre-PYPOST-793 pipeline
  (including stale `main.py` `PyPostStyle` claim). Deferred to Step 7 per architecture.
- **Broad `except Exception` in `StyleManager.load_styles`** — pre-existing; individual QSS
  read failures are logged and skipped rather than failing fast. Can mask partially loaded
  stylesheets.
- **`showEvent` deferred re-apply** — `QTimer.singleShot(0, apply_settings)` remains a Qt
  post-show polish workaround. Pre-existing; not introduced or worsened by this task.
- **`apply_appearance` does not log `theme` at the facade** — theme is logged only in
  `apply_theme`. Sufficient for diagnostics but requires reading two DEBUG lines to correlate
  full appearance state.

## Missing Tests

All new and updated test modules declare explicit timeouts via
`pytestmark = pytest.mark.timeout(60)` — **timeout blocker cleared**.

| Scenario | Status |
| --- | --- |
| Full pipeline call order (theme → styles → font) | Covered (`test_apply_appearance_call_order`) |
| Font survives `setStyleSheet` re-polish | Covered (`test_font_size_survives_stylesheet_reset`) |
| Font min / second-call-wins | Covered in `test_style_manager_appearance.py` |
| `MainWindow` delegates with correct `theme` / `font_size` | Covered (`test_apply_settings_font.py`) |
| Low-level `apply_theme` / `apply_styles` | Unchanged — existing style-manager tests |
| macOS native tab layout regression | Unchanged — `test_tab_layout_regression.py` |
| **`apply_appearance` DEBUG log output** | Not covered — low value; manual validation in Step 5 |
| **End-to-end `MainWindow` full pipeline without mocking `apply_appearance`** | Not covered — font assertions moved to `StyleManager` tests; acceptable trade-off |
| **Dark / light Fusion theme + full QSS integration** | Partial — `test_apply_appearance_stylesheet_contains_font_rule` uses light theme; tab layout tests focus on system/`PyPostStyle` path |

## Performance Concerns

None introduced. `apply_appearance` composes three existing synchronous calls with no new I/O.
`load_styles()` still reads all `.qss` files on every settings change (pre-existing).

## Follow-up Tasks

| Priority | Task | Rationale | Jira |
| --- | --- | --- | --- |
| Low | **Update `doc/dev/ui_font_and_styles.md`** — document `StyleManager.apply_appearance` as authoritative pipeline; remove stale `main.py` note | Completed in Step 7 | Done (PYPOST-793) |
| Low | **Evaluate `PyPostStyle.set_close_button_size`** — document override use case or remove dead API | Pre-existing from PYPOST-792; no production caller | [PYPOST-795](https://pypost.atlassian.net/browse/PYPOST-795) |
| Low | **Add Makefile `help` target** | Workspace Makefile rule compliance | [PYPOST-794](https://pypost.atlassian.net/browse/PYPOST-794) |
| Medium | **Improve `close.svg` contrast on dark tab chrome** | Accessibility / polish; unrelated to consolidation | [PYPOST-796](https://pypost.atlassian.net/browse/PYPOST-796) |
| Low | **Pre-existing: replace `print()` in `config_manager.py`** with structured logging | PYPOST-688 scope | [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) |

## Validation Summary

- `make check` passes (flake8 clean; **1569 tests passed**).
- All PYPOST-793 test modules have explicit timeout markers.
- R-P3-004 orchestration ownership gap closed — no duplicate appearance pipeline outside
  `StyleManager.apply_appearance`.
- No new technical debt blockers for Step 7.
