# PYPOST-999: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — verification debt closed with a green locking
test; no production change; explicit timeout markers present; no blockers.

Scope reviewed: `tests/test_environment_import.py` (new
`test_overwrite_import_reuses_unchanged_and_reencrypts_changed_hidden`),
`ai-tasks/PYPOST-999/*`, and cross-refs in `doc/dev/environments_dialog.md` /
`doc/dev/environment_encryption_at_rest.md` (Step 8).

## Shortcuts Taken

- **Green locking test (verification debt)** — Architecture and requirements
  expected the assertion to pass on current production; Step 3 still delivered
  the automated lock (not N/A). Step 4 was a no-op product change.
- **Single scenario with KEEP + CHANGE** — One integration test proves selective
  reuse on the preserved `id` (mirrors adapter unit style via `plan_import`).
- **Co-located in `test_environment_import.py`** — Preferred over a sibling
  module per architecture; accepts mixed unittest classes + pytest function
  already present in the file.
- **No UI / presenter coverage** — Explicitly out of scope; siblings
  PYPOST-1000 / PYPOST-1001 own presenter wiring and Import button clicks.

## Code Quality Issues

- **Module mixes `unittest.TestCase` and pytest functions** — Pre-existing from
  PYPOST-986; the new test follows the pytest style used by
  `load_import_candidates_*`. Optional future homogenization is not required
  for DoD.
- **Stale RED module docstring** — Fixed in Step 5 cleanup.

## Missing Tests

**No blocker.** Module-scope `pytestmark = pytest.mark.timeout(60)`.

| Scenario | Status |
| --- | --- |
| Overwrite preserves `id` + KEEP reuse + CHANGE re-encrypt + reload | Present |
| Adapter-only reuse / single-key re-encrypt | Pre-existing (adapter tests) |
| Large-env selective re-encrypt benchmark | Pre-existing (benchmark) |
| Overwrite id/position without encryption | Pre-existing (`TestPlanImportOverwrite`) |
| EnvPresenter `read_import_file` wiring | Sibling — already ticketed |
| Import… button mouseClick wiring | Sibling — already ticketed |
| Keep Both / Skip × encryption reuse | Out of scope (identity path is Overwrite) |

## Performance Concerns

None. Single Fernet-backed save/reload scenario (~10 ms locally).

## Deviations from Initial Architecture

None. Test-only delivery matches `20-architecture.md`:
`plan_import(OVERWRITE)` → `StorageManager.save_environments` → on-disk
envelope asserts → `load_environments`. No production API or format change.

## Hardcoded Values

Test-only fixture strings (`existing-dev-id`, `KEEP` / `CHANGE` plaintexts)
and local Fernet key via `monkeypatch` — appropriate for an isolated round-trip.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent debt: Overwrite × ciphertext reuse lock | This story (PYPOST-999) |
| EnvPresenter `read_import_file` wiring test | PYPOST-1000 |
| Import… button QTest.mouseClick wiring | PYPOST-1001 |

### NON-BLOCKER (optional; ticket only if desired)

None new that require tickets for DoD. Optional homogenization of
`test_environment_import.py` to all-pytest style can stay untracked until a
broader import-test cleanup.

### Accepted / out of scope (do not ticket)

- Production observability changes for this path
- Keep Both / Skip encryption round-trips
- UI click-level Overwrite × encryption e2e

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** (module timeout 60s) |
| Deviations from architecture | None |
| Acceptance gaps | **None** — DoD locking scenario green |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — CI now proves Overwrite identity + selective Hidden
envelope reuse/re-encrypt after save/reload; remaining import gaps are sibling
stories already ticketed under PYPOST-986.
