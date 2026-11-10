# PYPOST-1543: Technical Debt Analysis

## Shortcuts Taken

None. The edit removes the stored compiled-rule list and the
`path_selectors_count` debug field. Hierarchical rules are still tokenized
with an ephemeral `CompiledPathSelector` and inserted into
`PathSelectorTrie`. Compile debug and the 1388 catalog lock read
`PathSelectorTrie.size`. Live `matches` and `redact_tree` are unchanged.
That is the plan in `ai-tasks/PYPOST-1543/20-architecture.md`.

## Code Quality Issues

None. `CompiledPathSelector.raw` is still assigned in `__init__` and is
still unread. The attribute was already unread while the retained list
existed; this ticket only stopped storing the compiled object. It is
pre-existing. It is not a new ticket.

The shorthand `*` scan and an isolated trie catalog stay on PYPOST-1544
and PYPOST-1545.

## Missing Tests

None. `tests/test_pypost_1543_failing_repro.py` locks the absence of
`_path_selectors`, compile DEBUG with `trie_size` and without
`path_selectors_count`, and the current live mask decisions. The retargeted
1388 catalog lock asserts `engine._trie.size` for 400 distinct rules and
keeps the miss-heavy redact checks. The 1394 compile-log assertion keeps
`raw_count`, `bare_keys_count`, and `trie_size`.

Touched tests declare an explicit timeout:

- `tests/test_pypost_1543_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(30)`.
- `tests/test_pypost_1388_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(30)`.
- `tests/test_pypost_1394_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(60)`.

Thirty seconds is the pure-unit band for the 1543 module and the existing
1388 module mark. Sixty seconds is the existing module mark on the 1394
suite and was left in place.

## Performance Concerns

None. Dropping the retained list removes one compiled object per
hierarchical rule from engine state. Match and redact walks are unchanged.
The shorthand breadcrumb scan and wildcard fan-out stress stay on
PYPOST-1544 and PYPOST-1545.

## Follow-up Tasks

none

This change introduces no new follow-up. Removing the duplicate stored
list is the work of this ticket. `CompiledPathSelector.raw` staying unread
is pre-existing and is not filed again. Existing engine follow-ups stay on
PYPOST-1544 and PYPOST-1545. Other sprint work stays on PYPOST-1547,
PYPOST-1548, PYPOST-1549, PYPOST-1550, PYPOST-1551, PYPOST-1557, and
PYPOST-1558. Baseline and flaky tests stay on PYPOST-1474, PYPOST-1475,
PYPOST-1553, PYPOST-1554, PYPOST-1555, and PYPOST-1556. This step records
no pre-existing test failure.

The selector-engine guide already describes trie indexing and compile
DEBUG `trie_size`. It does not describe a retained compiled-rule list as
required for matching or for the efficiency check. That note is for
Step 8. It is not a follow-up ticket.
