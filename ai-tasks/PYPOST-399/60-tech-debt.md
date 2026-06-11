# PYPOST-399: Technical Debt Analysis

## Shortcuts Taken

- **Fixed colors** ([PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395)): Tests
  assert hardcoded QColor names; dark-theme migration will require test updates.
- **Heuristic JSON regex** ([PYPOST-393](https://pypost.atlassian.net/browse/PYPOST-393)):
  Tests document current behavior, not full JSON spec edge cases.

## Code Quality Issues

- None blocking. Test file mixes pytest mark with unittest — consistent with project Qt tests.

## Missing Tests

- Negative sign on numbers: regex may not color leading `-` separately (documented in
  `test_highlights_json_number`).
- Multi-line placeholders across blocks — out of scope (PYPOST-124).
- Visual/screenshot regression — deferred; format-range assertions suffice.

## Performance Concerns

- None for test additions.

## Deviations from Architecture

- None.

## Follow-up Tasks

No new follow-up Jira issues required. Source item from PYPOST-9 `40-tech-debt.md` is
resolved by this task.

## Blocker Review Verdict

**SAFE TO CLOSE** — JSON syntax test coverage extended; all tests pass; no production
changes required.
