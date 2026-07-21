# PYPOST-830: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Gateway surface aligned onto shared `qapp` via
`@pytest.mark.usefixtures("qapp")` on the three target `TestCase` modules. No
product changes. Items below are non-blocking follow-ups.
**Do not create Jira tickets in this step** — Phase D / tech-debt sync fills
the Jira column later.

## Shortcuts Taken

- **Kept `unittest.TestCase` + `usefixtures`.** Architecture preferred this over
  converting gateway checks to free functions with a `qapp` parameter
  (responsiveness style). Coverage intent and assertion style stayed the same;
  converting style is optional churn, not DoD.
- **Did not touch `tests/conftest.py`.** Reused the existing module-scoped
  singleton `qapp`; no session-scope or pytest-qt plugin swap.
- **Suite-wide Qt migration deferred.** Requirements/architecture explicitly
  out-of-scoped remaining `setUpClass` / local-`qapp` modules (presenters,
  editors, dialogs, etc.).
- **Full `make check` not re-asserted in Steps 4–5.** Step 3 ran full
  `make test` (1701 passed + 3 unrelated SOLID LOC failures); Steps 4–5 used
  scoped gateway + responsiveness isolation (20 passed), same pattern as
  PYPOST-827–829.
- **Intermittent hang not fixed here.** One full-suite stall on
  `test_save_async_emits_save_completed` (Qt GC / teardown) was observed once
  during Step 3, did not reproduce on retry or focused clusters, and is out of
  product/fixture-alignment scope — documented as TD-1.

## Code Quality Issues

- **Two shared-fixture consumption styles remain.** Responsiveness (and many UI
  modules) use `def test_...(qapp)`; gateway `TestCase` modules use
  `usefixtures("qapp")`. Both are valid pytest patterns; documented in
  architecture. Unifying style is optional polish (TD-3), not a defect.
- **Sibling worker module still module-local.**
  `tests/test_collection_storage_worker.py` still creates `QApplication` in
  `setUpClass`. It shares hang-resistant `process_until` (PYPOST-827) but was
  not in the PYPOST-830 gateway-surface list; aligning it is a small consistency
  follow-up (TD-2).
- **Broad suite still mixed.** ~35 test modules use `setUpClass` +
  `QApplication.instance() or QApplication([...])`; ~23 modules redefine a
  local `def qapp()` instead of importing the conftest fixture. Same consistency
  class as the debt this ticket closed for gateways — suite-wide only (TD-4).

No naming, structure, or coverage-intent regressions in the three aligned
modules. Timeout markers retained (`pytestmark = pytest.mark.timeout(120)`).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Env / collection gateway async load/save / queue | Covered (aligned modules) |
| H3 stress canary (≥200 cycles + GC) | Covered (aligned stress module) |
| Responsiveness reference (`qapp` param) | Covered (unchanged) |
| Explicit timeout markers on scoped modules | Covered |
| Regression for intermittent save_completed suite hang | Not covered — see TD-1 |
| Suite-wide shared-`qapp` migration | Out of scope |
| Convert gateway `TestCase` to free functions | Not required |
| Full `make check` green after SOLID noise clears | Deferred — see Already tracked / TD-5 |

**No timeout-marker blockers.**

## Performance Concerns

None introduced. Fixture alignment does not change wait budgets
(`process_until` / 5 s timeouts) or product worker teardown. H3 stress cost
unchanged (~12 s for both gateways).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Medium | Investigate intermittent full-suite hang on `test_save_async_emits_save_completed` | Step 3: one stall during full `make test`; sample suggested Qt GC / `QComboBox` teardown vs `EnvironmentStorageWorker` cross-thread deadlock. Did not reproduce on retry or presenter+gateway clusters. Not caused by `usefixtures` alignment (focused runs green). Reproduce under suite prefix, then harden teardown / wait / GC ordering | Jira: [PYPOST-883](https://pypost.atlassian.net/browse/PYPOST-883) |
| TD-2 | Low | Align `test_collection_storage_worker.py` onto shared `qapp` | Closest remaining storage Qt sibling still on `setUpClass`; same `usefixtures("qapp")` pattern as gateway units | Jira: [PYPOST-884](https://pypost.atlassian.net/browse/PYPOST-884) |
| TD-3 | Lowest | Optional: convert gateway `TestCase` modules to free functions with `qapp` param | Style-only; matches responsiveness. Not required for DoD | Jira: [PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885) |
| TD-4 | Low | Suite-wide migrate remaining `setUpClass` / local `qapp` modules onto conftest `qapp` | Out of scope for PYPOST-830. Inventory: ~35 modules with `setUpClass` `QApplication`; ~23 with duplicate local `def qapp()`. Prefer incremental batches (workers → presenters → editors) | Jira: [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) |
| TD-5 | Lowest | Re-run full `make check` when SOLID baseline noise is clear | Scoped gate used in Steps 4–5; not a DoD blocker for harness alignment — already tracked | Jira: [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Hang-resistant shared `process_until` | [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827) (done) |
| Enriched timeout diagnostics | [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) (done) |
| H3 worker finish teardown (`deleteLater` / short `wait`) | [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) (done) |
| Gateway shared-`qapp` alignment (this ticket) | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| SOLID LOC baseline failures (`main_window` / `env_presenter`) | Pre-existing quality-gate noise; historical SOLID / MainWindow split backlog (e.g. PYPOST-686 / 717 / 672 family). Unrelated to this harness change — do not reticket from PYPOST-830 |
| Optional shared finish-teardown helper | [PYPOST-881](https://pypost.atlassian.net/browse/PYPOST-881) |
| Full `make check` after sibling noise (829 deferral) | [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |

### Planned this ticket (not separate Debt)

- Step 7: briefly note `usefixtures("qapp")` for unittest gateway modules in
  GUI / testing dev docs if they still imply module-local `setUpClass` for this
  surface — not a Debt ticket.

## User documentation

N/A — test-harness consistency only; no `doc/user/` updates. Developer docs are
Step 7.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: env + collection gateway units and H3 stress obtain Qt via shared
  suite `qapp` (`usefixtures`); coverage intent preserved; no product change.
- TD-1 is a suite-flake investigation follow-up, not an acceptance failure for
  fixture alignment (retry and focused runs green).
- TD-2–TD-5 are consistency / polish / deferred gate items.
- No missing pytest timeout markers on scoped modules.
- SOLID baseline LOC failures are unrelated and already in the SOLID backlog
  class — not blockers for PYPOST-830.
