# PYPOST-973: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: collections-tree isolated harnesses tear down via shared
`detach_item_view_model` (`close_isolated_tree_actions` /
`isolated_tree_actions`); all harness call sites register cleanup; unit proofs
pass; `doc/dev/testing.md` documents adoption.

## Shortcuts Taken

- **unittest `addCleanup` instead of rewriting every test as a context
  manager** — Same close path; lower churn. Context manager remains available
  for pytest-style callers.
- **Did not migrate non-harness collections_tree imports** (FakeRequestManager
  etc. in presenter/import tests) — Those do not create isolated
  `QTreeView` harnesses.

## Code Quality Issues

None blocking. Close helper is small and reuses PYPOST-940 detach.

## Missing Tests

| Scenario | Status |
| --- | --- |
| close_isolated_tree_actions clears model | Covered |
| isolated_tree_actions context manager | Covered |
| Consumer call sites use addCleanup | Covered by migration + suite green |
| Qt warning regression across full suite | Not separately asserted (focused run clean) |

## Performance Concerns

None.

## Deviations from Architecture

None. Architecture plan delivered.

## Follow-up Tasks

### NON-BLOCKER

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Optionally migrate consumers to `isolated_tree_actions` context manager | Cosmetic consistency; addCleanup already guarantees teardown. Jira: [PYPOST-1043](https://pypost.atlassian.net/browse/PYPOST-1043) |

### Already tracked elsewhere (do not reticket)

| Area | Owner |
| --- | --- |
| Source PYPOST-940 TD-1 | This story (PYPOST-973) |
| Shared qt_item_view helper | [PYPOST-940](https://pypost.atlassian.net/browse/PYPOST-940) |

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None for acceptance |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE**
