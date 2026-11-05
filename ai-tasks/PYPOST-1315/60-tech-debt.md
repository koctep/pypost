# PYPOST-1315: Technical Debt Analysis

Scope: test-harness Qt dispose for export UI workers — `tests/helpers/qt_widget_dispose.py`,
wiring in `tests/test_environment_export_ui.py`, `tests/test_collection_export_ui.py`, and
`tests/test_environment_export_ui_teardown_repro.py`. Production `pypost/` unchanged.

**No item below is a BLOCKER.** Touched modules keep `pytestmark = pytest.mark.timeout(60)`.
The do-testing explicit-timeout rule is met. Phase D / tech-debt sync creates Jira issues;
this step only records candidates.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | Medium | `qt_activation.ActivatedWindow` still drains with `processEvents` only — same DeferredDelete class as pre-fix env export | yes (new) |
| TD-2 | Medium | No deterministic collections dispose contract (shiboken / topLevelWidgets); env-only repro | yes (new) |
| TD-3 | Medium | No negative control that incomplete dispose leaves a live `EnvironmentListWidget` | yes (new) |
| TD-4 | Low | Env export UI tests still `widget.close()` in every `finally` while autouse fixture runs `dispose_qt_root` | yes (new) |
| TD-5 | Low | Collections export UI repeats `dispose_collections_export_fixture` in ~19 `finally` blocks | yes (new) |
| TD-6 | Low | `dispose_collections_export_fixture(presenter: Any, …)` — duck-typed instead of `CollectionsPresenter` | yes (new) |
| TD-7 | Low | Contract test name still says “incomplete … dispose” but calls the fixed helper | yes (new) |
| TD-8 | Low | Module/session `topLevelWidgets` purge in `conftest` left out of scope (architecture note) | yes (new) |
| TD-9 | Lowest | Hardcoded `teardown(timeout_ms=50)` in collections dispose wrapper | yes (new) |
| TD-10 | Low | Bounded subprocess matrix never saw native `-11`/`-7` on this host; evidence remains contract-only | no (accepted for DoD; optional stronger CI stress later) |
| TD-11 | Medium | `make lint` does not flake8 `tests/` | yes | existing [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) |

## Shortcuts Taken

- **sendPostedEvents vs architecture’s qt_activation mirror.** Architecture proposed
  close → `processEvents` → `deleteLater` → `processEvents` to match
  `tests/helpers/qt_activation.py`. Step 4 found `processEvents` alone does not process
  DeferredDelete for `EnvironmentListWidget`; `QCoreApplication.sendPostedEvents(None,
  QEvent.Type.DeferredDelete)` was required for `shiboken6.isValid` to go false. Correct
  for the defect; leaves `qt_activation` on the weaker drain (TD-1).
- **Env double-close retained.** Each env export UI test still ends with `widget.close()` in
  `finally`; the autouse fixture then runs full `dispose_qt_root`. Harmless but redundant;
  cleanup step explicitly deferred polish (TD-4).
- **Collections dispose via duck typing.** Wrapper uses `getattr` / `Any` so tests do not
  import a hard type dependency at the helper boundary; works, but weakens static checks
  (TD-6).
- **Collections contract repro deferred.** Architecture allowed a sibling
  `test_collection_export_ui_teardown_repro.py` once shared defect was confirmed. Step 4
  fixed collections wiring without a parallel deterministic contract test (TD-2).
- **Native SIGSEGV not reproduced in bound.** Host matrix (≤5 children) archived all-zero
  exits; DoD allows contract **A** as the mandatory gate. Stronger parallel/disk-pressure
  evidence is optional, not required to close this task (TD-10).

## Code Quality Issues

- **TD-1 (Medium) — weaker dispose still in `qt_activation`.**
  `ActivatedWindow.__exit__` does close → `processEvents` → `deleteLater` → `processEvents`
  without `sendPostedEvents(DeferredDelete)`. Export UI now uses the stronger helper; other
  GUI tests that rely on `ActivatedWindow` may still leave live C++ objects until process
  exit under load. Follow-up: route activation teardown through `dispose_qt_root` (or share
  the DeferredDelete drain) and add a small contract assertion if cheap.
- **TD-5 (Low) — collections finally boilerplate.** Every test manually calls
  `dispose_collections_export_fixture(presenter, qapp)`. An autouse fixture (pattern already
  used for env `_created_widgets`) would shrink duplication and reduce missed-teardown risk
  when new tests are added.
- **TD-6 (Low) — `Any` presenter parameter.** Prefer
  `CollectionsPresenter` (or a narrow Protocol with `teardown` / `widget` / `panel`) for
  mypy and call-site clarity.
- **TD-7 (Low) — misleading test name.**
  `test_incomplete_env_dispose_leaves_no_live_environment_list_widget` documents the old red
  path; body now asserts the *complete* dispose contract. Rename to match behavior (e.g.
  `test_dispose_qt_root_destroys_environment_list_widget`).
- **TD-9 (Lowest) — magic `timeout_ms=50`.** Match nearby presenter-lifecycle budgets or a
  named constant; not a functional risk for idle export UI tests.

No unexplained product architecture deviations: production export paths untouched; shared
helper + collections `teardown()` reuse match the selected design once DeferredDelete drain
is accounted for.

## Missing Tests

- **TD-2 (Medium) — collections dispose contract.** No
  `shiboken6.isValid(panel)` / leftover `topLevelWidgets` assertion for the collections
  export fixture path. Env has
  `tests/test_environment_export_ui_teardown_repro.py`; collections relies on green suite
  exit only. Follow-up: add a focused contract module (or parametrize the env repro) covering
  `dispose_collections_export_fixture`.
- **TD-3 (Medium) — incomplete-dispose negative control.** After the fix, nothing fails if
  someone weakens `dispose_qt_root` back to close + single `processEvents` (the original
  env fixture shape). A small unit test that applies incomplete cleanup and expects a live
  root (or asserts DeferredDelete was drained) would lock the helper’s necessity.
- **Timeouts:** not missing.

  | Module | Marker |
  | --- | --- |
  | `tests/helpers/qt_widget_dispose.py` | N/A (helper) |
  | `tests/test_environment_export_ui.py` | `pytestmark = timeout(60)` |
  | `tests/test_collection_export_ui.py` | `pytestmark = timeout(60)` |
  | `tests/test_environment_export_ui_teardown_repro.py` | `pytestmark = timeout(60)` |

- **TD-11:** test modules are outside `make lint` flake8 `pypost/` scope — existing
  [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303); do not re-file.

## Performance Concerns

- Dispose adds a short event-loop drain per created root / collections fixture. Negligible
  vs GUI test body cost; no follow-up.
- Bounded subprocess matrix runs the full env export UI file up to five times (≤120s each
  child). Acceptable for evidence; not a CI default path beyond the repro module.

## Architecture / harness remainder

- **TD-8 (Low) — session-level widget purge.** Architecture listed module/session
  `topLevelWidgets` cleanup in `conftest` as out of scope / future debt. A harness-wide
  purge would reduce similar post-PASS crashes elsewhere but is a broader policy change
  than this ticket’s export UI dispose fix.
- **Disk-pressure twin.** Collection export was included because it shared the close-only
  dispose class. If future crashes under disk pressure persist *after* dispose wiring with
  a distinct root cause (I/O, OOM), treat that as a separate investigation — not silently
  assumed fixed by this helper alone.

## Follow-up Tasks

Specific tasks for Phase D / tech-debt Jira sync (do **not** create issues in Step 7):

1. **TD-1 — Align `qt_activation` teardown with DeferredDelete drain** (Medium)  
   Use `dispose_qt_root` (or equivalent `sendPostedEvents(DeferredDelete)`) in
   `ActivatedWindow.__exit__` / related helpers so non-export GUI tests do not keep the
   weaker processEvents-only sequence.  
   Jira: [PYPOST-1478](https://pypost.atlassian.net/browse/PYPOST-1478)

2. **TD-2 — Collections export dispose contract test** (Medium)  
   Add a deterministic repro/contract asserting panel invalidity and no leftover export UI
   roots after `dispose_collections_export_fixture` (sibling to env teardown repro).  
   Jira: [PYPOST-1479](https://pypost.atlassian.net/browse/PYPOST-1479)

3. **TD-3 — Negative control for incomplete Qt dispose** (Medium)  
   Assert that close / `deleteLater` / single `processEvents` without DeferredDelete drain
   still leaves a live `EnvironmentListWidget`, so `dispose_qt_root` cannot be silently
   weakened.  
   Jira: [PYPOST-1480](https://pypost.atlassian.net/browse/PYPOST-1480)

4. **TD-4 — Drop redundant env `widget.close()` finally blocks** (Low)  
   Rely on autouse `_cleanup_widgets` → `dispose_qt_root` only.  
   Jira: [PYPOST-1481](https://pypost.atlassian.net/browse/PYPOST-1481)

5. **TD-5 — Autouse fixture for collections export dispose** (Low)  
   Replace repeated per-test `finally` dispose calls with a shared fixture pattern.  
   Jira: [PYPOST-1482](https://pypost.atlassian.net/browse/PYPOST-1482)

6. **TD-6 — Type the collections dispose helper** (Low)  
   Replace `Any` with `CollectionsPresenter` or a small Protocol.  
   Jira: [PYPOST-1483](https://pypost.atlassian.net/browse/PYPOST-1483)

7. **TD-7 — Rename env dispose contract test** (Low)  
   Name should describe complete `dispose_qt_root` success, not “incomplete dispose”.  
   Jira: [PYPOST-1484](https://pypost.atlassian.net/browse/PYPOST-1484)

8. **TD-8 — Optional conftest top-level widget purge** (Low)  
   Evaluate module/session end purge of orphan `topLevelWidgets` while `qapp` is alive;
   separate from export-UI-specific dispose.  
   Jira: [PYPOST-1485](https://pypost.atlassian.net/browse/PYPOST-1485)

9. **TD-9 — Named constant for collections teardown budget** (Lowest)  
   Replace bare `timeout_ms=50` with a shared lifecycle constant if budgets are
   consolidated elsewhere.  
   Jira: [PYPOST-1486](https://pypost.atlassian.net/browse/PYPOST-1486)

10. **TD-11 — Test lint coverage** (Medium, existing)  
    Tracked by [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303); do not
    duplicate.

**Accepted / no new ticket:** TD-10 (bounded matrix all-zero on this host; DoD already
satisfied by contract gate).

## User documentation

N/A for this step — no user-facing product change. Step 8 owns `doc/dev/` notes linking
export UI dispose to existing Qt teardown helpers.

## Independent Closure Review

Left for the gate owner / review subagent. This execution leaves STEP 7 `[/]` and does not
create Jira issues.
