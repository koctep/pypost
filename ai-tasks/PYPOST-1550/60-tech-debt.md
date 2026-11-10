# PYPOST-1550: Technical Debt Analysis

## Shortcuts Taken

None. Production modules were not changed. The characterization tests
in `tests/test_pypost_1550_medium_indent_preserve.py` follow
`ai-tasks/PYPOST-1550/20-architecture.md`. An indent change redisplays
the longer response with reveal memory kept. The background completion
restores a revealed value and leaves a hidden value masked. A late
completion whose generation is no longer current returns before it
replaces the document.

## Code Quality Issues

None. The stale test calls
`ResponseView._on_mask_formatting_completed` with the generation taken
from the first display, and it reads `_mask_worker` and
`_mask_format_generation`. That call is the production generation
check. When `generation` differs from `_mask_format_generation`, the
slot returns before `setText` and `set_masked_spans`. Cooperative
interruption often drops the worker signal, so the check is reached by
delivering the older generation to that slot. `tests/test_response_mask_worker.py`
already reads those two fields. Assertions after the call use the
status label, the plain text, and `is_revealed`. No production name or
structure was added. This access is not new debt, and no ticket is
filed for it.

## Missing Tests

None. Both required outcomes are in the new module, and both passed:

- `test_medium_indent_keeps_reveal_choices` reveals `token`, leaves
  `password` hidden, then changes indent. After the background format
  is applied, the token stays visible and the password stays masked.
- `test_stale_background_result_leaves_newer_display` shows a newer
  display, reveals one value, then delivers the older generation.
  Status, text, and both reveal flags stay on that newer display.

The module declares an explicit timeout:

- `tests/test_pypost_1550_medium_indent_preserve.py` uses
  `pytestmark = pytest.mark.timeout(60)`.

Sixty seconds is the GUI tier and the mark named in the architecture.
The marker is the signal default. The module does not set
`method="thread"`. Both collected tests use that module marker.
`process_until` is bounded at 10 seconds. `worker.wait` is bounded at
10 seconds.

Clearing the body and short-response re-mask stay on the tests for
PYPOST-1549. Pruning leftover reveal keys stays on PYPOST-1551. This
change does not leave a new gap in either of those.

## Performance Concerns

None. Production modules were not changed. The longer body is one JSON
object padded into the existing medium band. The indent case runs the
worker the product already starts. The stale case does not apply a
second format to the document.

## Follow-up Tasks

none

This change introduces no new follow-up. No Jira issue was created.
PYPOST-1551 already covers leftover reveal keys and is not re-filed.
This step records no pre-existing test failure.

`doc/user/requests.md` still describes click-to-reveal, re-mask, and
the plain-text path for payloads larger than 100 KB. It does not state
a false indent or stale-result rule, so `doc/` was left unchanged.
Developer docs are Step 8.
