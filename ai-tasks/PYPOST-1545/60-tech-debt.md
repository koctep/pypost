# PYPOST-1545: Technical Debt Analysis

## Shortcuts Taken

None. This task adds the characterization catalog in
`tests/test_pypost_1545_failing_repro.py` only. Production matching in
`pypost/core/json_selector_engine.py` stays as it is. The catalog inserts
tokens from `CompiledPathSelector`, reads trie size and the two walks, and
compares those answers with `JsonSelectorEngine.matches`. Removed match
helpers stay absent. That is the plan in
`ai-tasks/PYPOST-1545/20-architecture.md`.

## Code Quality Issues

None. The catalog is table-driven and stays on the methods named in the
architecture. It does not call `_step`, `_compile`, `_parse_tokens`, or
`_sequence_has_wildcard`, and it does not read `_trie`, `_bare_keys`, or
`_root`.

`CompiledPathSelector.raw` is still assigned in `__init__` and is still
unread. The catalog reads `.tokens` only. The attribute was already unread
before this ticket. It is pre-existing and already classified.

## Missing Tests

None. `tests/test_pypost_1545_failing_repro.py` locks insert dedupe and
size, an empty index, shorthand-only walks, the direct hit for
`items.*.secret`, bare-name rules, path-and-key agreement with the public
check, the wildcard-heavy yes-or-no, and the absence of the removed
helpers.

The module declares an explicit timeout:

- `tests/test_pypost_1545_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(30)`.

Thirty seconds is the pure-unit band. Every collected test in that module
is covered by the module marker.

## Performance Concerns

None as new work. The wildcard-heavy catalog locks today's yes-or-no for
four rules. It sets no speed or memory target and adds no fan-out
structure. `PathSelectorTrie._step` still builds a fresh list and set of
active nodes per token. That allocation is pre-existing, production
matching is unchanged, and a new index shape stays out of scope for this
ticket.

## Follow-up Tasks

none

This change introduces no new follow-up. The isolated catalog is the work
of this ticket. `CompiledPathSelector.raw` staying unread is pre-existing
and stays classified as it already is. Other sprint work stays on
PYPOST-1547, PYPOST-1548, PYPOST-1549, PYPOST-1550, PYPOST-1551,
PYPOST-1557, and PYPOST-1558. Baseline and flaky tests stay on
PYPOST-1474, PYPOST-1475, PYPOST-1553, PYPOST-1554, PYPOST-1555, and
PYPOST-1556. This step records no pre-existing test failure.

The selector-engine guide already describes trie indexing and the public
mask check. A note that this catalog exists is for Step 8. It is a
documentation note for that step.
