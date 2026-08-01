# PYPOST-903: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: parametrized caplog matrix covers catalog install name tokens
beyond `golden_ok` (`seed_get_ok`, `seed_post_ok`, `double_body_lock_ok`,
`url_router`, explicit custom `name=`). Module timeout marker present. No
production changes; no blockers.

## Shortcuts Taken

- **Single parametrized test.** One function + `_INSTALL_MATRIX` table instead
  of per-token sibling tests — DRY caplog boilerplate.
- **One custom name sample.** `scenario_alpha` stands in for arbitrary author
  overrides; exhaustive custom-name permutations not required.
- **Unit path only.** No live GUI re-assert of install events (same as
  PYPOST-870 scope).

## Code Quality Issues

- None material. Matrix follows PYPOST-870 / PYPOST-867 caplog style.
- `_InstallCase` tuple type alias keeps parametrize table readable.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Catalog `golden_ok` | Covered (PYPOST-870; retained in matrix) |
| Catalog `seed_get_ok` | Covered (this ticket) |
| Catalog `seed_post_ok` | Covered (this ticket) |
| Catalog `double_body_lock_ok` | Covered (this ticket) |
| Mapping → `name=url_router` | Covered (this ticket) |
| Explicit custom `name=` | Covered (this ticket) |
| Live GUI path re-assert | Not covered (optional; unit sufficient) |
| Callable `side_effect` install name | Not covered (optional; uses `custom` name path) |

No timeout-marker blockers.

## Performance Concerns

None. Six pure unit caplog rows; sub-millisecond each.

## Follow-up Tasks

### Already tracked (do not reticket)

Sibling optional debt from PYPOST-870:
[PYPOST-904](https://pypost.atlassian.net/browse/PYPOST-904) — live GUI path
re-assert (if ever needed).

### NON-BLOCKER

None new. Matrix closes the PYPOST-870 optional name-token gap.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(10)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefix intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR7 and DoD satisfied.
