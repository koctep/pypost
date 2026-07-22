# PYPOST-885: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Gateway and H3 stress modules converted from `unittest.TestCase` +
`usefixtures("qapp")` to free pytest functions with a `qapp` parameter,
matching responsiveness. No product changes. Items below are non-blocking
follow-ups.
**Do not create Jira tickets in this step** — Phase D / tech-debt sync fills
the Jira column later.

## Shortcuts Taken

- **Did not convert collection worker `TestCase`.** Worker remains on
  `usefixtures("qapp")` (PYPOST-884); same optional polish class, out of this
  ticket’s three-module scope.
- **Did not touch `tests/conftest.py`.** Reused the existing module-scoped
  singleton `qapp`.
- **Suite-wide TestCase migration deferred.** Remaining presenter/editor
  `TestCase` + `usefixtures` modules stay as valid consumers.
- **Full `make check` not re-asserted.** Steps 3–5 used scoped guard + gateway
  + stress + responsiveness isolation (**23 passed**), same pattern as
  PYPOST-830 / PYPOST-884.

## Code Quality Issues

- **Two shared-fixture consumption styles remain suite-wide.** Gateways/H3/
  responsiveness now use `def test_...(qapp)`; workers/presenters/editors still
  use `usefixtures("qapp")` on `TestCase`. Both are valid; unifying more
  surfaces is optional polish (TD-1).
- **Broad suite still mixed.** Suite-wide shared-`qapp` migration remains
  PYPOST-886 (lifecycle), distinct from this style polish.

No naming, structure, or coverage-intent regressions in the converted modules.
Timeout markers retained (`pytestmark = pytest.mark.timeout(120)` on
gateway/stress; `timeout(10)` on style guard).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Env / collection gateway async load/save / queue | Covered (converted modules) |
| H3 stress canary (≥200 cycles + GC) | Covered (converted stress module) |
| Responsiveness reference (`qapp` param) | Covered (unchanged; included in scoped run) |
| Source guard for free-function style | Covered (new style guard) |
| Convert worker `TestCase` to free functions | Not required — see TD-1 |
| Suite-wide shared-`qapp` migration | Out of scope (PYPOST-886) |
| Full `make check` green after SOLID noise clears | Deferred — PYPOST-882 |

**No timeout-marker blockers.**

## Performance Concerns

None introduced. Style conversion does not change wait budgets
(`process_until` / 5 s timeouts) or product worker teardown. H3 stress cost
unchanged (~13 s for both gateways in scoped run).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Lowest | Optional: convert collection worker `TestCase` to free functions with `qapp` param | Same style polish as this ticket; worker was out of scope | Unticketed — create only if maintainers want worker parity |
| TD-2 | Low | Suite-wide migrate remaining `setUpClass` / local `qapp` modules onto conftest `qapp` | Lifecycle consistency; distinct from free-function style | Already tracked: [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) |
| TD-3 | Lowest | Re-run full `make check` when SOLID baseline noise is clear | Scoped gate used in Steps 4–5; not a DoD blocker | Already tracked: [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |

### Unticketed follow-ups

- TD-1 only (optional worker style polish). Do not create in this step — Phase D
  / tech-debt sync owns Jira creation if desired.

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Gateway shared-`qapp` alignment | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) (done) |
| Collection worker shared-`qapp` | [PYPOST-884](https://pypost.atlassian.net/browse/PYPOST-884) (done) |
| Gateway free-function style (this ticket) | [PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885) |
| Suite-wide shared-`qapp` migration | [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) |
| Full `make check` after sibling noise | [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |
| Hang-resistant shared `process_until` | [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827) (done) |

### Planned this ticket (not separate Debt)

- Step 8: update GUI / testing / storage-async docs so gateway/H3 modules are
  listed under free-function `qapp` (not `usefixtures`).

## User documentation

N/A — test-harness consistency only; no `doc/user/` updates. Developer docs are
Step 8.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: env + collection gateway units and H3 stress use free pytest
  functions with `qapp`; coverage intent preserved; style guard green; no
  product change.
- TD-2–TD-3 are already-ticketed; TD-1 is optional out-of-scope polish.
- No missing pytest timeout markers on scoped modules.
