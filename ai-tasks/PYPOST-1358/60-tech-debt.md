# PYPOST-1358: Technical Debt Analysis

Scope: registry + autouse `dispose_qt_root` for the environment **list/import**
suite and the list teardown repro —
`tests/test_environment_list_widget.py`,
`tests/test_environment_list_widget_teardown_repro.py`
(reuse of `tests/helpers/qt_widget_dispose.py`). Production `pypost/` unchanged.

**No item below is a BLOCKER.** Touched modules keep explicit timeout markers
(`pytestmark = pytest.mark.timeout(60)`; B overrides with
`@pytest.mark.timeout(360)`). The do-testing explicit-timeout rule is met.
Phase D / tech-debt sync creates or closes Jira issues; this step only records
candidates.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | Low | List/import suite still `widget.close()` in every `finally` while autouse runs `dispose_qt_root` | no new — retarget [PYPOST-1481](https://pypost.atlassian.net/browse/PYPOST-1481) to include list suite (same class as env-export TD-4) |
| TD-2 | Low | A-complete and R-dispose bodies are now identical (`dispose_qt_root` + desired end-state) | [PYPOST-1500](https://pypost.atlassian.net/browse/PYPOST-1500) |
| TD-3 | Low | Teardown-repro comments still describe list suite as close-only-only; suite now also disposes via registry/autouse | **addressed in Step 8** (comment sync) |
| TD-4 | Low | `doc/dev/export_ui_qt_dispose.md` (+ helper module docstring) omit list/import registry/autouse | **addressed in Step 8** |
| TD-5 | Low | `_created_widgets` / `_make_widget` / `_cleanup_widgets` copied from env-export suite | [PYPOST-1501](https://pypost.atlassian.net/browse/PYPOST-1501) |
| TD-6 | Lowest | B zero-crash subprocess matrix on this host; original SIGSEGV/SIGBUS mix not captured in-bound | no (accepted DoD diagnostic) |
| TD-7 | Low | Module/session `topLevelWidgets` purge in `conftest` still out of scope | no new — existing [PYPOST-1485](https://pypost.atlassian.net/browse/PYPOST-1485) |
| TD-8 | Medium | Pre-existing: `make lint` does not flake8 `tests/` | no new — existing [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) |
| TD-9 | Medium | Other GUI suites still close-only (e.g. `test_environment_variables_widget.py`, request-editor widgets) — same DeferredDelete class risk | [PYPOST-1502](https://pypost.atlassian.net/browse/PYPOST-1502) |
| — | — | PYPOST-1315 TD-3 incomplete-dispose negative control for `EnvironmentListWidget` | **addressed here** — A-incomplete in list teardown repro; Phase D close/verify [PYPOST-1480](https://pypost.atlassian.net/browse/PYPOST-1480) |

## Shortcuts Taken

- **Finally + autouse retained (belt and suspenders).** Step 4 wired
  `_created_widgets` + autouse `dispose_qt_root` (R-dispose / H1) but kept every
  product-suite `finally: widget.close()` to mirror the env-export pattern from
  PYPOST-1315. Harmless and idempotent with full dispose afterward; leaves
  thirteen redundant close sites (TD-1), same class as export TD-4 /
  [PYPOST-1481](https://pypost.atlassian.net/browse/PYPOST-1481).
- **A-complete and R-dispose kept as separate members.** Architecture required
  permanent positive guard vs suite-teardown red→green contract. After Step 4
  both call `dispose_qt_root` and the same desired-end-state asserts; bodies are
  duplicate (TD-2). Cleanup step explicitly deferred merge to preserve contract
  names and history.
- **Per-suite registry copy.** List suite copied the env-export
  `_created_widgets` / `_make_widget` / `_cleanup_widgets` scaffold rather than
  extracting a shared helper (TD-5). Faster R-dispose land; duplicates harness
  with `tests/test_environment_export_ui.py`.
- **Diagnostic B, not live SIGSEGV.** Bounded subprocess matrix recorded
  zero-crash exits on this host (architecture / DoD allow the diagnostic
  artifact). Original affected crash mix remains uncaptured in-bound (TD-6).
- **Docs deferred to Step 8 (then completed).** Architecture and observability
  noted the export dispose doc omitted list/import; Steps 4–6 left TD-3 / TD-4
  for Step 8, which extended the doc, helper docstring, and repro comments.

## Code Quality Issues

- **TD-1 (Low) — redundant `widget.close()` finally blocks.**
  All thirteen list/import tests still end with `finally: widget.close()` while
  autouse `_cleanup_widgets` runs full `dispose_qt_root` (which itself starts
  with `close()`). Follow-up: drop the repeated finally closes once registry
  autouse remains the durable missed-teardown guard. Prefer retargeting
  [PYPOST-1481](https://pypost.atlassian.net/browse/PYPOST-1481) to cover both
  env-export and list/import suites rather than filing a duplicate ticket.
- **TD-2 (Low) — duplicate A-complete / R-dispose bodies.**
  `test_a_complete_environment_list_dispose_reaches_desired_end_state` and
  `test_r_dispose_suite_close_only_reaches_desired_end_state` now share the same
  dispose + assert path. Keep both names as durable guards, or collapse to one
  shared helper call / parametrized member while preserving polarities in
  module docs. R-dispose name still says `close_only` though the body applies
  the suite dispose helper — rename when consolidating.
- **TD-5 (Low) — duplicated env-widget dispose scaffolding.**
  Export and list suites each own an identical module-level registry + autouse.
  Follow-up: extract a small shared fixture/helper (e.g. under
  `tests/helpers/`) used by both product suites (and optionally teardown
  repros) so future `EnvironmentListWidget` modules do not copy-paste again.

No unexplained architecture deviations: cause fork **R-dispose** (H1);
A-complete / A-incomplete / R-dispose / B polarities preserved; production
import behavior untouched; helper reused without inventing a second
DeferredDelete sequence.

## Missing Tests

- **Timeouts:** not missing.

  | Module | Marker |
  | --- | --- |
  | `tests/test_environment_list_widget.py` | `pytestmark = timeout(60)` |
  | `tests/test_environment_list_widget_teardown_repro.py` | `pytestmark = timeout(60)`; B `@pytest.mark.timeout(360)` |
  | `tests/helpers/qt_widget_dispose.py` | N/A (helper) |

- **Incomplete-dispose negative control (former PYPOST-1315 TD-3 /
  PYPOST-1480):** **covered** by
  `test_a_incomplete_environment_list_close_only_leaves_residual_liveness` in
  the list teardown repro (asserts residual `shiboken6.isValid` + leftovers,
  then disposes in `finally` so later tests stay clean). Phase D should
  close or verify PYPOST-1480 as done by this ticket — do not re-file the
  same negative control.
- **No additional product-assertion coverage gaps** for the thirteen
  list/import nodes; assertions and timeouts were preserved by design.
- **TD-9 (Medium) — sibling close-only GUI suites.** Outside this ticket’s
  charter but the same DeferredDelete class remains elsewhere (e.g.
  `tests/test_environment_variables_widget.py`, request-editor GUI modules).
  Follow-up: inventory unparented top-level roots that still use close-only
  teardown and wire `dispose_qt_root` (or registry/autouse) where evidence
  warrants — do not silently assume list/import fix covers them.

## Performance Concerns

- Dispose adds a short event-loop drain per created list widget. Negligible vs
  GUI test body cost; no follow-up.
- Bounded subprocess matrix runs the full list/import file up to three times
  (≤120s each child) under B’s 360s override. Acceptable for evidence; not a
  CI default path beyond the repro module.

## Architecture / harness remainder

- **TD-7 (Low) — session-level widget purge.** Architecture and prior tickets
  listed module/session `topLevelWidgets` cleanup in `conftest` as out of
  scope. Still tracked by [PYPOST-1485](https://pypost.atlassian.net/browse/PYPOST-1485);
  do not re-file.
- **TD-4 / TD-3 — docs and stale comments.** Addressed in Step 8:
  `doc/dev/export_ui_qt_dispose.md` covers list/import registry/autouse; helper
  module docstring is no longer export-only; teardown-repro comments distinguish
  close-only negative control from product suite full teardown.
- **Related-ticket clarity.** PYPOST-1315 / PYPOST-1357 remain the export /
  collections owners. This ticket closed the list/import gap on the shared
  helper; coordinated remaining-gap work is TD-9 inventory, not a rewrite of
  those tickets.

## Follow-up Tasks

Specific tasks for Phase D / tech-debt Jira sync (do **not** create issues in
Step 7):

1. **TD-1 — Drop redundant list/import `widget.close()` finally blocks** (Low)  
   Rely on autouse `_cleanup_widgets` → `dispose_qt_root` only (keep registry
   registration in `_make_widget`). Prefer updating
   [PYPOST-1481](https://pypost.atlassian.net/browse/PYPOST-1481) to include
   `tests/test_environment_list_widget.py` rather than a duplicate ticket.

2. **TD-2 — Deduplicate or rename A-complete / R-dispose contract members** (Low)  
   Share one assert helper (or parametrize) while keeping durable positive-guard
   vs suite-teardown documentation; rename R-dispose away from `close_only` now
   that the suite dispose path is wired.  
   Jira: [PYPOST-1500](https://pypost.atlassian.net/browse/PYPOST-1500)

3. **TD-5 — Shared env-widget dispose registry helper** (Low)  
   Extract the `_created_widgets` / `_make_*` / autouse pattern used by env
   export and list/import into one reusable test helper so new
   `EnvironmentListWidget` suites do not copy-paste.  
   Jira: [PYPOST-1501](https://pypost.atlassian.net/browse/PYPOST-1501)

4. **TD-9 — Inventory remaining close-only Qt GUI suites** (Medium)  
   Audit other offscreen GUI modules that create unparented roots with
   `close()`-only teardown; apply `dispose_qt_root` + registry/autouse where
   the same post-PASS native-crash class is plausible.  
   Jira: [PYPOST-1502](https://pypost.atlassian.net/browse/PYPOST-1502)

5. **TD-7 / TD-8 — Existing harness / lint debt** (Low / Medium)  
   - [PYPOST-1485](https://pypost.atlassian.net/browse/PYPOST-1485) (conftest
     top-level purge)  
   - [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) (`make lint`
     flake8 for `tests/`)  
   Do not duplicate.

6. **Phase D close/verify prior tickets addressed by this work**  
   - [PYPOST-1480](https://pypost.atlassian.net/browse/PYPOST-1480) (PYPOST-1315
     TD-3 negative control) — satisfied by list A-incomplete.  
   - Optionally confirm [PYPOST-1481](https://pypost.atlassian.net/browse/PYPOST-1481)
     scope includes list/import when polishing finally blocks.

**Accepted / no new ticket:** TD-6 (B zero-crash matrix on this host; DoD
already satisfied by contract gate + five-consecutive isolated suite streak).

**Step 8 (not Debt tickets):** TD-3 / TD-4 — **done** in Step 8
(`doc/dev/export_ui_qt_dispose.md`, helper module docstring, teardown-repro
comments aligned to list/import registry/autouse).

## User documentation

N/A — no user-facing product change. Developer docs extended in Step 8
(`doc/dev/export_ui_qt_dispose.md` covers list/import).

## Independent Closure Review

Left for the gate owner / review subagent. This execution leaves STEP 7 `[/]`
and does not create Jira issues.
