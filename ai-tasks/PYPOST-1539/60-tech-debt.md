# PYPOST-1539: Technical Debt Analysis

## Shortcuts Taken

None. On the path branch, `validate_field_selector` rejects a literal `..`
in the stripped text before `_normalize_wildcards`, and it returns the
existing unsupported result. The collapse loop and `strip(".")` stay so
`users[*].email` and `[*].id` remain acceptable. That is the chosen
design in `ai-tasks/PYPOST-1539/20-architecture.md`.

## Code Quality Issues

None. The late `..` check in `_validate_path` stays as the unchanged
backstop. Header selectors, the simple-key check, suggestions, and the
masking engine are unchanged. Reusing `_UNSUPPORTED_MESSAGE` is the
accepted wording. Specialized messages belong to
[PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540).

## Missing Tests

None. `tests/test_pypost_1539_failing_repro.py` asserts `users..email` is
not ok and `users[*].email` is ok. `tests/test_field_selector_syntax.py`
already locks `users[*].email` and `[*].id`.

The repro module declares `pytestmark = pytest.mark.timeout(30)`. That
explicit marker is present coverage. Thirty seconds sits in the pure-unit
band. The marker is not missing-test debt.

## Performance Concerns

None. The new check is one substring test on the stripped selector. The
collapse loop is the same short-string rewrite it was before this task.

## Follow-up Tasks

None.

No new task is opened.
[PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540) already owns
specialized invalid messages. The masking engine staying more permissive
than the verdict is the accepted split from PYPOST-1387. This step records
no pre-existing test failure. User docs in `doc/user/requests.md` list
supported forms and do not call `users..email` acceptable. Developer notes
in `doc/dev/` are Step 8.
