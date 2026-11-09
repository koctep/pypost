# PYPOST-1540: Technical Debt Analysis

## Shortcuts Taken

None. `_message_for_draft` returns a kind sentence only when the stripped
draft matches exactly one shape: a `[?` filter, a leading `$`, or a
`[-?\d+]` index. A mix such as `$.users[0].name` keeps
`_UNSUPPORTED_MESSAGE`. A written `..` returns that same generic warning
before normalization. Both choices are the design in
`ai-tasks/PYPOST-1540/20-architecture.md`.

## Code Quality Issues

None. The helper is private to `pypost/core/field_selector_syntax.py`.
Accept and reject stay on the existing branches. The header branch,
`_SUGGESTIONS`, and the masking engine are unchanged. The three sentences
are module constants. The repro repeats them as literals, which is what
the architecture required.

## Missing Tests

None. `tests/test_pypost_1540_failing_repro.py` locks the dollar, index,
and filter sentences, and it locks a quiet `token`.
`tests/test_field_selector_syntax.py` still locks supported forms and
invalid guidance for mixed, index, and filter drafts.
`tests/test_pypost_1539_failing_repro.py` locks that `users..email` is
rejected while `users[*].email` stays ok.

The new module declares `pytestmark = pytest.mark.timeout(30)`. That
explicit marker is present. Thirty seconds sits in the pure-unit band.

## Performance Concerns

None. Choosing the sentence is a substring check and one compiled regex
on the stripped selector. The same check runs for an accepted path and
then drops the unused string. Selector text is short.

## Follow-up Tasks

None.

This change introduces no new follow-up. It is the specialized-message
work already tracked here (follow-up 4 of PYPOST-1387). The generic
warning for a mixed shape and for a written `..` stays the accepted
design. Existing sprint work stays on PYPOST-1542, PYPOST-1543,
PYPOST-1544, PYPOST-1545, PYPOST-1547, PYPOST-1548, PYPOST-1549,
PYPOST-1550, PYPOST-1551, PYPOST-1557, and PYPOST-1558. Baseline and
flaky tests stay on PYPOST-1474, PYPOST-1475, PYPOST-1553, PYPOST-1554,
PYPOST-1555, and PYPOST-1556. This step records no pre-existing test
failure.

## Notes for Step 8

Step 8 should record the three kind sentences in
`doc/dev/hidden_fields_table.md`. The line that the existing unsupported
message is reused remains accurate for a written `..`. User docs in
`doc/user/requests.md` list supported forms and do not quote the generic
warning. This note is for Step 8. It is not a follow-up ticket.
