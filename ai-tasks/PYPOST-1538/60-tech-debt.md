# PYPOST-1538: Technical Debt Analysis

## Shortcuts Taken

None. `pypost/core/header_selector_prefix.py` owns `HEADER_SELECTOR_PREFIX`
and `header_selector_name`. The function re-reads that module global on
each call. `validate_field_selector`, `JsonSelectorEngine._compile`, and
`sanitize_headers` recognize a header only by calling
`header_selector_name`. The production prefix remains `header:`.

## Code Quality Issues

None. The source assertion and the patched-prefix check in
`tests/test_header_selector_prefix.py` are the accepted design. Suggestion
and error strings that mention `header:Authorization` stay public examples.
Each caller keeps its own leading-whitespace policy.

## Missing Tests

None. `test_three_call_sites_use_one_header_selector_prefix` requires the
three call sites to call `header_selector_name`, then requires validation,
selection, and sanitization to follow one patched prefix.

The module declares `pytestmark = pytest.mark.timeout(30)`. That explicit
marker is present coverage. Thirty seconds sits in the pure-unit band.

## Performance Concerns

None. Each recognition is one case-insensitive prefix check and a slice of
`len(prefix)`. The three call sites keep the empty-name, skip, and redact
policies they already had.

## Follow-up Tasks

None.

[PYPOST-1539](https://pypost.atlassian.net/browse/PYPOST-1539) already owns
literal `..` rejection.
[PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540) already owns
specialized invalid messages. This step records no pre-existing test
failure. User docs under `doc/user/` do not describe this prefix, and the
prefix people write stays `header:`. Developer notes in `doc/dev/` are
Step 8.
