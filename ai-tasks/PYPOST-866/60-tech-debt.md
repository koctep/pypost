# PYPOST-866: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Harness table↔mark set-equality guard meets DoD: table matches marked
modules, maintenance note in `doc/dev/agent_e2e.md`, unit guard with
module timeout, Steps 1–8 artifacts. No production code changes.

## Shortcuts Taken

- **AST mark discovery, not `pytest --collect-only`.** Faster and
  Qt-free; matches how marks are applied today (module `pytestmark` /
  decorators). Runtime collection plugins are out of scope.
- **Module path set equality only.** Covers column prose stays editorial
  (FR2); guard does not validate Covers text quality.
- **Does not auto-generate the markdown table.** Curated Covers notes
  preserved; authors update rows when marks change.
- **Guard stays unmarked / out of the harness table.** Same placement as
  PYPOST-864 seed inventory drift guard.

## Code Quality Issues

- Table parse anchors on prose “Harness modules under the marker” then
  `| Module |` rows — rename of that heading would break the guard
  (intentional coupling; failure message names the missing anchor).
- AST discovery covers module `pytestmark` and function/class decorators
  named `agent_e2e`; exotic mark forms (e.g. imported aliases) are not
  scanned — none exist in this suite today.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Mark set == table Module paths | Covered |
| Missing doc / missing anchor / empty table | Covered (asserts) |
| Guard itself unmarked / not in table | Covered by set equality |
| Covers column quality | Manual (FR2) |
| Runtime `pytest -m agent_e2e` collect parity | Out of scope (AST) |

No timeout-marker blockers.

## Performance Concerns

None. Pure unit AST + one markdown read; runs under default `make test`.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Seed inventory code↔doc guard | PYPOST-864 (done) |
| Marker / packaging origin | PYPOST-858 (done); this debt closed here |

### NON-BLOCKER

None requiring new Jira tickets this run. Optional future hardening
(runtime collect-only parity, Covers lint) can wait until demanded.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | AST + set equality — intentional |
| Missing tests with timeout markers | **None** — module `timeout(10)` |
| Deviations from architecture | None — Option: cheap test + doc note |
| Hardcoded values | Anchor string / table header — intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 satisfied by aligned table, maintenance note,
and drift guard in `make test`.
