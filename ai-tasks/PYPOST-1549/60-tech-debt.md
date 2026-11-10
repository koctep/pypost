# PYPOST-1549: Technical Debt Analysis

## Shortcuts Taken

None. Production modules were not changed. The characterization tests
call `ResponseView.clear_body`, `display_response`, `handle_click`, and
`set_indent_size` as they already work. That matches
`ai-tasks/PYPOST-1549/20-architecture.md`.

## Code Quality Issues

None. `tests/test_pypost_1549_clear_and_remask.py` keeps the harness
from `tests/test_pypost_1392_failing_repro.py`: one `ResponseView`,
small JSON, `handle_click` at `start_pos + 1`, and `view.close()` in
`finally`. `_span_by_path` uses the same path substring match the
parent already accepted for these flat fixtures. No production naming,
structure, or hardcoded behavior was added.

## Missing Tests

None. Both required outcomes are in the new module:

- `test_clear_body_forgets_reveal_for_matching_body` reveals one field,
  calls `clear_body`, then shows the same body text. Both spans start
  masked and neither secret is in the text.
- `test_remask_stays_hidden_across_indent_reformat` re-masks one field,
  leaves a second revealed, leaves a third untouched, then calls
  `set_indent_size(4)`. The re-masked value stays hidden, the left
  reveal stays visible, and the untouched value stays masked.

The module declares an explicit timeout:

- `tests/test_pypost_1549_clear_and_remask.py` uses
  `pytestmark = pytest.mark.timeout(60)`.

Sixty seconds is the GUI tier and the mark named in the architecture.
The marker is the signal default. The module does not set
`method="thread"`. Both collected tests use that module marker. There
is no `threading.Event` and no polling loop.

## Performance Concerns

None. The bodies stay small, so display uses `format_masked_json` on
the calling thread. No new worker, no new restore loop, and no new
stored map. Production cost is unchanged.

## Follow-up Tasks

none

This change introduces no new follow-up. No Jira issue was created.
PYPOST-1550 and PYPOST-1551 already exist and stayed out of scope.
This step records no pre-existing test failure.

`doc/user/requests.md` still describes click-to-reveal and
click-to-re-mask as they work. It does not state a false clear-body or
re-mask rule, so `doc/` was left unchanged. Developer docs are Step 8.
