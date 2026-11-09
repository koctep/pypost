# PYPOST-1542: Technical Debt Analysis

## Shortcuts Taken

None. The edit removes `PathSelectorTrie.matches_tokens` and
`CompiledPathSelector.matches`. The five older matcher checks in
`tests/test_pypost_1394_failing_repro.py` now call
`JsonSelectorEngine.matches` with the same expected results. Segment
checks on `CompiledPathSelector.tokens` stay. `_step`, `_parse_tokens`,
`tokens`, `_path_selectors`, `matches_path_and_key`, and
`matches_shorthand_path_and_key` stay in use. That is the plan in
`ai-tasks/PYPOST-1542/20-architecture.md`.

## Code Quality Issues

None. Production masking still answers through `JsonSelectorEngine.matches`.
Redaction and the response viewer keep that call. `CompiledPathSelector.raw`
remains stored on the compiled rule and unread. The attribute was already
unread while `matches` read `tokens` only. This ticket's delivered work is
the removal of the two unused match helpers. The dual compile list, the
shorthand `*` scan, and a separate trie catalog stay on PYPOST-1543,
PYPOST-1544, and PYPOST-1545.

## Missing Tests

None. `tests/test_pypost_1542_failing_repro.py` locks the absence of both
helpers and the five live outcomes. The retargeted
`test_compiled_path_selector_tokenization_and_matching` keeps the segment
checks and those same five booleans.

Both the new module and the retargeted module declare an explicit timeout:

- `tests/test_pypost_1542_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(30)`.
- `tests/test_pypost_1394_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(60)`.

Thirty seconds is the pure-unit band for the new module. Sixty seconds is
the existing module mark on the 1394 suite and was left in place.

## Performance Concerns

None. Redaction and the response viewer still call the same live walks.
Match cost is unchanged. The shorthand breadcrumb scan and the extra
compiled-rule list stay on PYPOST-1544 and PYPOST-1543.

## Follow-up Tasks

none

This change introduces no new follow-up. Removing the two unused helpers is
the work of this ticket. Existing engine follow-ups stay on PYPOST-1543,
PYPOST-1544, and PYPOST-1545. Other sprint work stays on PYPOST-1547,
PYPOST-1548, PYPOST-1549, PYPOST-1550, PYPOST-1551, PYPOST-1557, and
PYPOST-1558. Baseline and flaky tests stay on PYPOST-1474, PYPOST-1475,
PYPOST-1553, PYPOST-1554, PYPOST-1555, and PYPOST-1556. This step records
no pre-existing test failure.

The selector-engine guide already describes compile tokenization and the
live walks. User docs do not name the removed helpers. That note is for
Step 8. It is not a follow-up ticket.
