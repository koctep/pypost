# PYPOST-721: Code Cleanup

## Changes

No production code changed — only new test files added, following existing
conventions (`pytestmark = pytest.mark.timeout(60)`, `qapp` fixture from
`tests/conftest.py`, dialogs closed in `finally` blocks).

## Verdict

No additional cleanup needed.
