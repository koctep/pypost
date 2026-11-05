# PYPOST-1311: Technical Debt Analysis

Scope: test-only harness fence for env-persistence temp-dir cleanup under encrypted
async load — `tests/test_env_persistence_tempdir_cleanup_repro.py` and the named
scenario in `tests/test_env_persistence_e2e.py` (`wait_storage_idle` + `teardown`
before `TemporaryDirectory` exit). Production `pypost/` is unchanged.

**No item below is a BLOCKER.** Both touched modules declare explicit module-level
timeouts (`pytestmark = pytest.mark.timeout(60)` on the repro;
`pytestmark = pytest.mark.timeout(120)` on the e2e module). The do-testing
explicit-timeout rule is met. Phase D / tech-debt sync creates Jira issues; this
step only records candidates.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | Medium | Durable repro has no negative control that cleanup fails without the fence | yes (new) |
| TD-2 | Low | Sibling e2e tests create `EnvPresenter` without `teardown` | yes (new) |
| TD-3 | Low | Hardcoded / inconsistent idle+teardown budgets (5s vs 30s) | yes (new) |
| TD-4 | Low | Fence pattern duplicated across repro try-path, repro `finally`, and e2e | yes (new) |
| TD-5 | Lowest | Repro `_GatedWorkspaceStorage` swallows `OSError` while writing | no (accepted for race double) |
| TD-6 | Lowest | Residual import-block order in e2e after Step 5 cleanup | no (cosmetic) |
| TD-7 | Medium | `make lint` does not flake8 `tests/` | yes | existing [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) |

## Shortcuts Taken

- **Test-only fence, no product change.** Architecture selected reuse of public
  `EnvPresenter.wait_storage_idle` / `teardown` rather than storage redesign or
  `TemporaryDirectory(ignore_cleanup_errors=True)` as primary fix. Correct for the
  defect; leaves production lifecycle APIs unchanged and places the burden on every
  future encrypted-async test author to remember the same ordering (TD-2, TD-4).
- **Green-only durable contract.** Step 3 was red without the fence; Step 4 applied
  release + idle + teardown so the repro stays green. There is no remaining test that
  deliberately omits the fence and expects `OSError` / Directory not empty (TD-1).
- **Manual `TemporaryDirectory` in the repro.** Explicit `tmp.cleanup()` asserts the
  cleanup contract; `finally` uses `shutil.rmtree(..., ignore_errors=True)` so a failed
  assert path does not cascade. Slightly different shape than the e2e `with` context
  manager — intentional, not a product deviation.
- **Gated storage write loop.** The double keeps creating/writing subtrees under the
  workspace while held, catching `OSError` and continuing so the race remains live
  even if cleanup starts early (TD-5).

## Code Quality Issues

- **TD-3 (Low) — magic timeout budgets.** Repro uses `wait_storage_idle(timeout_ms=5_000)`
  and `teardown(timeout_ms=5_000)`; named e2e uses `wait_storage_idle(timeout_ms=30_000)`
  and `teardown(timeout_ms=5_000)`. All stay inside module timeouts; naming a shared
  constant (or documenting why e2e needs a longer idle budget under suite load) would
  reduce drift.
- **TD-4 (Low) — duplicated fence sequence.** The same release/idle/teardown ordering
  appears in the repro happy path, the repro `finally`, and the e2e `try`/`finally`.
  Architecture allowed an optional local helper; none was extracted. A tiny helper
  (or documented one-liner pattern in Step 8 docs) would cut copy-paste risk when
  new encrypted-load e2e scenarios are added.
- **TD-5 (Lowest) — swallowed `OSError` in the gated double.** Acceptable for a
  race-forcing storage stub; not production code. No follow-up ticket.
- **TD-6 (Lowest) — e2e import grouping.** Step 5 fixed the leading blank and rough
  stdlib → third-party → local order; local `pypost.*` imports are still not
  strictly package-sorted. Cosmetic only while `make lint` skips `tests/` (TD-7).
- **No architecture deviation.** Selected test-only fence matches
  `20-architecture.md`; no production API or encryption behavior change.

## Missing Tests

- **TD-1 (Medium) — negative control for the cleanup race.** After the fix, nothing
  fails if someone removes `wait_storage_idle` / `teardown` from the named e2e (or
  weakens the repro’s try-path fence while leaving a soft `finally`). A small
  contract that holds the gate, calls `TemporaryDirectory.cleanup()` *without*
  idle+teardown, and expects `OSError` / errno 39 (then releases + fences) would
  lock the fence’s necessity the way Step 3 did transiently. Follow-up: add an
  explicit “incomplete fence leaves cleanup failing” case in the repro module (or
  a sibling), with a hard timeout marker.
- **Sibling e2e scenarios (TD-2).** `test_env_with_hidden_keys_survives_presenter_save_and_restart`
  builds presenters and calls `load_environments()` without `teardown`. Per
  architecture those paths are sync (encryption off) and were out of flake scope;
  they still leave presenter/gateway lifecycle unfenced. Low risk today; follow-up
  hygiene if encrypted async spreads to sibling tests.
- **Timeouts:** not missing.

  | Module | Marker |
  | --- | --- |
  | `tests/test_env_persistence_tempdir_cleanup_repro.py` | `pytestmark = timeout(60)` |
  | `tests/test_env_persistence_e2e.py` | `pytestmark = timeout(120)` |

- **Product assertion coverage:** named e2e still asserts no environment shown when
  the key is missing for encrypted data (US3 / DoD). No coverage gap for the ticket
  DoD.
- **TD-7:** test modules are outside `make lint` flake8 `pypost/` scope — existing
  [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303); do not re-file.

## Performance Concerns

- Named e2e may wait up to 30s for storage idle after encrypted load dispatch; under
  normal conditions the missing-key path settles far sooner. Budget is bounded and
  fits the 120s module timeout. No production performance impact (`pypost/`
  unchanged).
- Repro gated write loop is CPU/FS-local and released within 5s idle budget; acceptable
  for a durable contract module. No follow-up.

## User documentation

N/A for this step — no user-facing product change. Step 8 owns `doc/dev/` notes
linking the env-persistence temp-dir fence to existing
[`presenter_teardown.md`](../../../doc/dev/presenter_teardown.md) /
[`testing.md`](../../../doc/dev/testing.md) guidance (wait_idle is sync, not a
substitute for `teardown`).

## Follow-up Tasks

Specific tasks for Phase D / tech-debt Jira sync (do **not** create issues in Step 7):

1. **TD-1 — Negative control for incomplete temp-dir fence** (Medium)  
   Add a durable assertion that omitting `wait_storage_idle` + `teardown` while an
   encrypted async load still owns the workspace makes `TemporaryDirectory.cleanup()`
   fail with Directory not empty / errno 39, then release and fence so the module
   stays suite-safe.  
   Jira: [PYPOST-1503](https://pypost.atlassian.net/browse/PYPOST-1503)

2. **TD-2 — Fence sibling env-persistence e2e presenters** (Low)  
   Call `teardown` (and idle when encryption/async is involved) for presenters in
   other tests in `tests/test_env_persistence_e2e.py`, or document why sync-only
   paths are exempt.  
   Jira: [PYPOST-1504](https://pypost.atlassian.net/browse/PYPOST-1504)

3. **TD-3 — Named constants for idle/teardown budgets** (Low)  
   Replace bare `5_000` / `30_000` ms literals with shared or module-level named
   budgets and a one-line rationale for the longer e2e idle wait.  
   Jira: [PYPOST-1505](https://pypost.atlassian.net/browse/PYPOST-1505)

4. **TD-4 — Shared fence helper for encrypted async + temp dir** (Low)  
   Extract a small test helper (local to env persistence tests or under
   `tests/helpers/`) that runs wait_idle → teardown before temp-dir exit, matching
   the documented presenter teardown contract.  
   Jira: [PYPOST-1506](https://pypost.atlassian.net/browse/PYPOST-1506)

5. **TD-7 — Test lint coverage** (Medium, existing)  
   Tracked by [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303); do not
   duplicate.

**Accepted / no new ticket:** TD-5 (OSError swallow in race double), TD-6 (cosmetic
import order).

## Independent Closure Review

Left for the gate owner / review subagent. This execution leaves STEP 7 `[/]` and does
not create Jira issues.
