# PYPOST-827: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- **Generic timeout assertion text kept.** Shared `process_until` still raises a fixed
  `AssertionError` (`condition not met within {timeout_ms}ms …`) without busy/pending or
  worker context. Acceptable hang defense; richer diagnostics remain
  [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828).
- **No production gateway/worker lifecycle change.** `_on_worker_finished` still clears the
  worker without `deleteLater()` / short `wait()`. H3 was not required for DoD; remains
  [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829).
- **Sibling modules keep module-local `QApplication` via `setUpClass`.** Unification onto
  the shared `qapp` fixture was explicitly out of scope; remains
  [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830).
- **Hang-regression tests left in the responsiveness module.** Architecture preferred
  keeping wall-clock / posted-quit proofs near the proven suite path rather than moving
  them next to `tests/helpers/process_until.py`. Not a compromise on hang defense — one
  shared definition is what consumers call.

No other shortcuts. Extraction and rewire matched architecture option B.

## Code Quality Issues

- **Assertion message is env-load biased.** Failure text still mentions
  `load_completed/load_failed` even though collection gateway/worker consumers use the
  same helper. Cosmetic; fold into richer diagnostics under PYPOST-828 rather than a
  separate ticket.
- **One unrelated nested `QEventLoop` remains timer-only.**
  `tests/test_env_presenter.py::test_async_load_refreshes_combo_when_encryption_enabled`
  still pumps `exec()` with a QTimer poll and **no** wall-clock deadline / posted quit.
  Same hang class as pre-PYPOST-823/827 siblings, but outside this task’s three-module
  DoD. Tracked as [PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877).

No naming, structure, or copy-drift issues in the shared helper or the four wired
modules. Local `_process_until` copies in the three siblings are gone.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Wall-clock deadline exits nested `exec()` | Covered (responsiveness) |
| Posted quit without poll timer | Covered (responsiveness) |
| Encrypted load/save responsiveness | Covered |
| Three sibling modules call shared helper | Covered (rewired; business assertions unchanged) |
| Stuck gateway with busy/pending in assertion text | Not covered (PYPOST-828) |
| Production `deleteLater` / `wait` after worker finish | Not added (PYPOST-829) |
| Env-presenter async load nested wait hang defense | Not covered — **new** debt |
| Dedicated `tests/helpers/test_process_until.py` | Not added — hang regressions already cover the helper |

All four wired modules keep `pytestmark = pytest.mark.timeout(120)` (signal method).
`test_env_presenter.py` already has `pytestmark = pytest.mark.timeout(60)`. No
timeout-marker blockers for this task.

## Performance Concerns

None introduced. Shared helper uses the same dual-deadline pattern as PYPOST-823
(default 5 s for siblings; responsiveness keeps explicit 10 s / 300 ms where needed).
Hang-regression waits stay ~300 ms by design. Focused suite: **20 passed** in ~1 s
(Step 4 validation).

## Follow-up Tasks

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Richer timeout diagnostics (busy/pending, optional worker state; neutralize env-biased message) | Low | Existing — do not recreate. Jira: [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) |
| Gateway worker `deleteLater` / short `wait` on finish (H3) | Low | Existing — do not recreate. Jira: [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) |
| Align remaining gateway tests on shared `qapp` fixture | Low | Existing — do not recreate. Jira: [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| Port `process_until` into env-presenter async-load nested wait | Medium | **NEW** — `test_env_presenter.py` still uses timer-only `QEventLoop.exec()`; same hang class. Jira: [PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877) |
| Update `doc/dev/gui_testing.md` (and related) to point at shared helper | — | Planned Step 7 work for this task, not a separate Debt ticket |

## User documentation

N/A — harness-only change; no `doc/user/` updates. Developer docs are Step 7.

## Blocker Review

**Verdict: SAFE TO CLOSE**

- DoD met: three siblings + responsiveness share hang-resistant `process_until`; focused
  suite green; no production behavior change required.
- Existing follow-ups PYPOST-828 / 829 / 830 remain relevant and open (To Do); linked
  above, not recreated.
- One **new** Medium follow-up (env-presenter nested wait) is out-of-DoD suite hygiene,
  not an acceptance blocker for PYPOST-827.
- Timeout markers present on all touched modules; no Step 6 testing blockers.
