# PYPOST-884: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Collection storage worker tests aligned onto shared `qapp` via
`@pytest.mark.usefixtures("qapp")`. No product changes. Items below are
non-blocking follow-ups.
**Do not create Jira tickets in this step** — Phase D / tech-debt sync fills
the Jira column later.

## Shortcuts Taken

- **Kept `unittest.TestCase` + `usefixtures`.** Same as PYPOST-830 gateway units;
  did not convert to free functions with a `qapp` parameter.
- **Did not touch `tests/conftest.py`.** Reused the existing module-scoped
  singleton `qapp`.
- **Suite-wide Qt migration deferred.** Remaining `setUpClass` / local-`qapp`
  modules (presenters, editors, dialogs, etc.) stay under PYPOST-886.
- **Full `make check` not re-asserted.** Steps 3–5 used scoped worker +
  alignment + collection gateway isolation (7 passed), same pattern as
  PYPOST-830.

## Code Quality Issues

- **Two shared-fixture consumption styles remain.** Responsiveness uses
  `def test_...(qapp)`; storage `TestCase` modules use `usefixtures("qapp")`.
  Both are valid; unifying style is optional polish (already ticketed as
  PYPOST-885 for gateways; applies equally to this worker).
- **Broad suite still mixed.** Suite-wide migration remains PYPOST-886.

No naming, structure, or coverage-intent regressions in the aligned module.
Timeout markers retained (`pytestmark = pytest.mark.timeout(120)` on worker;
`timeout(10)` on alignment guard).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Worker load finished / failed | Covered (aligned module) |
| Source guard for shared-`qapp` alignment | Covered (new alignment module) |
| Collection gateway sibling (smoke) | Covered in Step 4 scoped run |
| Suite-wide shared-`qapp` migration | Out of scope (PYPOST-886) |
| Convert worker `TestCase` to free functions | Not required |
| Full `make check` green after SOLID noise clears | Deferred — PYPOST-882 |

**No timeout-marker blockers.**

## Performance Concerns

None introduced. Fixture alignment does not change wait budgets
(`process_until` / 5 s timeouts) or product worker teardown.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Lowest | Optional: convert collection worker `TestCase` to free functions with `qapp` param | Style-only; matches responsiveness. Same class as PYPOST-885 | Already tracked: [PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885) (gateway style polish; extend or reuse if desired) |
| TD-2 | Low | Suite-wide migrate remaining `setUpClass` / local `qapp` modules onto conftest `qapp` | Out of scope for PYPOST-884 | Already tracked: [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) |
| TD-3 | Lowest | Re-run full `make check` when SOLID baseline noise is clear | Scoped gate used in Steps 4–5; not a DoD blocker | Already tracked: [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |

### Unticketed follow-ups

None. All follow-ups above are already tracked in Jira.

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Gateway shared-`qapp` alignment | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) (done) |
| Collection worker shared-`qapp` (this ticket) | [PYPOST-884](https://pypost.atlassian.net/browse/PYPOST-884) |
| Optional TestCase → free-function style | [PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885) |
| Suite-wide shared-`qapp` migration | [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) |
| Full `make check` after sibling noise | [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |
| Hang-resistant shared `process_until` | [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827) (done) |

### Planned this ticket (not separate Debt)

- Step 8: update GUI / testing / storage-async docs so the collection worker is
  listed under `usefixtures("qapp")` (not still on `setUpClass`).

## User documentation

N/A — test-harness consistency only; no `doc/user/` updates. Developer docs are
Step 8.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: collection storage worker units obtain Qt via shared suite `qapp`
  (`usefixtures`); coverage intent preserved; alignment guard green; no product
  change.
- TD-1–TD-3 are already-ticketed polish / deferred gate items.
- No missing pytest timeout markers on scoped modules.
