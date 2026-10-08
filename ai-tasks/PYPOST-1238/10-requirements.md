# PYPOST-1238: Prevent false ownership-check success

## Goals

Give maintainers reliable evidence that the ownership suite checks the flat child finder.
A check of a different finder must not count as coverage of the flat child finder merely
because a local variable has a similar name. This closes TD-4 from PYPOST-1041 and prevents
misleading green results when ownership assertions are reorganized.

## User Stories

- As a maintainer, I want unrelated finder checks rejected as evidence of flat child finder
  coverage so that a passing ownership guard reflects the intended verification.
- As a maintainer, I want the existing supported references to the flat child finder accepted
  so that valid ownership checks continue to pass.

## Definition of Done

- AC-1: A check of the tree finder through a local named `child_fn`, without checking the flat
  child finder, is rejected as evidence of flat child finder delegation coverage.
- AC-2: Bare references named exactly `find_child` and `find_child_index_by_display_text`
  remain recognized as supported references to the flat child finder.
- AC-3: Other bare references are not recognized solely because their names contain `child`,
  regardless of letter case.
- AC-4: The existing supported lookup-expression form referring to
  `find_child_index_by_display_text` remains recognized.
- AC-5: Both delegation and duplicate-display-role ownership checks apply the same reference
  recognition behavior. The existing valid ownership suite continues to pass.
- AC-6: An automated regression demonstrates rejection of the misleading tree-finder-only
  example and the existing checks pass after the correction.
- AC-7: Application behavior and Qt interactions remain unchanged.

## Task Description

### Problem and scope

The ownership regression guard can report flat child finder coverage when only the tree
finder is checked through a misleading local name. The intended outcome is to distinguish
supported flat child finder references from unrelated references in the test guard.

The scope is reference recognition and its focused regression coverage in
`tests/test_display_role_scan_ownership_repro.py`. Broader mutation-matrix work tracked in
PYPOST-1236, production changes, and Qt changes are excluded.

### Language and constraints

- Implementation language: Python.
- Preserve current accepted direct names and lookup-expression coverage.
- Keep checks deterministic and suitable for the existing fast test suite.
- Execute validation through repository Makefile targets.
- No performance or security behavior change is required.

### Main entities

- Maintainer: relies on ownership checks when reviewing changes.
- Flat child finder: the function whose delegation and display-role ownership are verified.
- Tree finder: a separate function whose verification cannot replace flat finder coverage.
- Ownership guard: accepts or rejects evidence that the intended finder is checked.

### Scenarios

1. A maintainer runs the current ownership suite with its supported flat finder references;
   the ownership guard recognizes the checks.
2. A maintainer rewrites a delegation assertion to examine only the tree finder through
   `child_fn`; the ownership guard rejects this as flat finder coverage.
3. A supported flat finder lookup expression is used; existing recognition is preserved.

## Q&A

- Why is this needed? PYPOST-1041 TD-4 documents a confirmed false green that can conceal
  missing flat finder verification. The Jira scope supplies this business reason.
- What stays outside this task? Production and Qt changes and the PYPOST-1236 mutation matrix.
- Source: [PYPOST-1041 technical debt](../PYPOST-1041/60-tech-debt.md), TD-4.
