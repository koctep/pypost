# PYPOST-823: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- **Scoped the hang fix to one module.** Hardened `_process_until` only in
  `tests/test_env_storage_responsiveness.py` (wall-clock deadline + daemon
  `threading.Timer` posting `QTimer.singleShot(0, loop, loop.quit)`). Sibling
  gateway/worker tests still use the pre-fix QTimer-only helper. Enough to
  restore the encrypted-load responsiveness gate; suite-wide helper unification
  deferred.
- **Generic timeout assertion text.** Architecture Phase A called for actionable
  failure context (busy/pending flags, optional worker state). The helper asserts
  a fixed message (`condition not met within {timeout_ms}ms …`) without reading
  gateway state. Acceptable for hang defense; richer diagnostics deferred.
- **No production gateway lifecycle change (H3).** `_on_worker_finished` still
  clears `self._worker = None` without `deleteLater()` / short `wait()`. Phase B
  was conditional on suite reproduction of missing `load_*` signals; Step 3 did
  not confirm H3, so product code was left unchanged.

## Code Quality Issues

- **Three sibling `_process_until` copies remain vulnerable to the same hang
  class** (nested `QEventLoop.exec()` + QTimer-only deadline; no wall-clock /
  posted quit):
  - `tests/test_environment_storage_gateway.py`
  - `tests/test_collection_storage_gateway.py`
  - `tests/test_collection_storage_worker.py`
  Prefer extracting a shared test helper (or porting the hardened helper) rather
  than leaving three outdated copies.
- **Gateway unit tests still use a module-local `QApplication`** via
  `setUpClass` instead of the shared `qapp` fixture pattern used by the
  responsiveness module after this task.
- **Worker lifecycle hygiene** in `EnvironmentStorageGateway._on_worker_finished`
  (and the collection gateway analogue, if present) remains a latent risk under
  heavy Qt suite churn; tracked as optional follow-up, not required for DoD.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Wall-clock deadline exits nested `exec()` | Covered |
| Posted quit without poll timer | Covered |
| Encrypted load/save responsiveness | Covered |
| Sibling modules' old `_process_until` hang defense | Not covered (helpers unchanged) |
| Stuck gateway with busy/pending in assertion text | Not covered (deferred diagnostics) |
| Production `deleteLater` / `wait` after worker finish | Not added (H3 not confirmed) |
| Full `make check` after suite-noise tickets land | Not re-run yet — see Follow-up |

All tests in the touched module keep `pytestmark = pytest.mark.timeout(120)`
(signal method). No timeout-marker blockers.

**Quality-gate gap:** This task verified `make test` end-to-end (hang gone; see
Suite Verification). A clean green `make check` (`analyze` + `test`) was not
re-asserted after documenting the three unrelated tabs-presenter failures. Re-run
`make check` once those failures are fixed on their own tickets, so the gate is
green without excluding out-of-scope noise.

## Performance Concerns

None introduced. Hang-regression tests wait ~300 ms by design; wall-clock bounds
keep failure under ~2 s. Default wait remains 10 s for load/save responsiveness.

Full `make test` completed in ~84 s with no hang / no indefinite Qt event-loop
stall — the PYPOST-823 hang class is gone from the suite run.

## Suite Verification

Ran full `make test` on 2026-07-21 (local, offscreen Qt via project defaults):

| Metric | Result |
| ------ | ------ |
| Duration | ~84 s (no hang) |
| Passed | 1643 |
| Failed | 3 |
| Deselected | 1 |
| Warnings | 1 (Starlette/`httpx` deprecation in MCP ASGI compat test) |

**In-scope (PYPOST-823):** All five `tests/test_env_storage_responsiveness.py`
tests passed, including wall-clock / posted-quit hang regressions and encrypted
load/save responsiveness. Suite finished normally; the previous indefinite hang
did not recur.

**Out of scope (other tickets):** The three failures are in
`tests/test_tabs_presenter.py` and are unrelated to env-storage / `_process_until`
hardening:

- `TestTabsPresenter::test_close_rightmost_of_three_tabs_does_not_land_on_plus`
- `TestTabsPresenter::test_close_rightmost_of_two_tabs_does_not_land_on_plus`
- `TestTabsPresenter::test_handle_close_tab_closes_current`

All three assert post-close focus must not land on the plus-tab index. They belong
to the tab close-focus workstream (PYPOST-818 / 819 / 820 / 822 and follow-ups),
not this hang fix. Do not treat them as PYPOST-823 blockers.

## Follow-up Tasks

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Port hardened `_process_until` (or extract shared helper) to sibling gateway/worker tests | Medium | Same hang class as PYPOST-823 if Qt timers stall mid-suite. Jira: [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827) |
| Richer timeout diagnostics (busy/pending, optional worker state) in wait helper | Low | Architecture Phase A item 2; improves triage when waits fail. Jira: [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) |
| Gateway worker `deleteLater` / short `wait` on finish (H3) | Low | Only if suite shows stranded `load_*` / `save_*` signals. Jira: [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) |
| Align remaining gateway tests on shared `qapp` fixture | Low | Consistency with responsiveness module; reduces duplicate app lifecycle. Jira: [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| Fix tabs-presenter close-focus failures (land-on-plus assertions) | Medium | Out of scope here; [PYPOST-824](https://pypost.atlassian.net/browse/PYPOST-824) / [PYPOST-825](https://pypost.atlassian.net/browse/PYPOST-825) / [PYPOST-826](https://pypost.atlassian.net/browse/PYPOST-826) |
| Re-run `make check` after tabs-presenter failures are green | Low | Missing quality-gate confirmation while suite has unrelated noise |

Debt follow-ups created from this analysis: PYPOST-827–830.

## Blocker Review

**Verdict: SAFE TO CLOSE**

- Encrypted-load responsiveness check is time-bounded; hang defense verified by
  dedicated regression tests and a full `make test` run (~84 s, hang gone).
- Scope stayed test-harness; no encryption policy or persistence changes.
- Three `test_tabs_presenter` failures are unrelated and owned by other tickets;
  they do not block PYPOST-823 acceptance.
- Deferred items above are follow-ups, not acceptance blockers.
- User documentation: N/A (test harness only; no `doc/user` change).
- Timeout markers present on the touched module; no Step 6 testing blockers.
