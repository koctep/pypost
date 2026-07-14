# PYPOST-798: Code Cleanup

## Production code

No production code changes. Tests-only task.

## Test code review

- New tests follow existing `unittest.TestCase` + module-level `pytestmark = pytest.mark.timeout(60)`.
- Docstrings on fallback tests clarify intent (primary vs fallback path).
- No duplicate setup — reuses `_make_header`, `_make_presenter`, `_plus_tab_index`.
- Negative test prevents over-broad `_on_tab_bar_clicked` behavior.

## Lint / style

- No new flake8 issues expected (test-only additions matching file conventions).
- Pre-existing E402 pattern (pytestmark before imports) unchanged.

## Validation

- Targeted: `make test PYTEST_ARGS="tests/test_tab_header.py tests/test_tabs_presenter.py -k plus_tab -v"`
- Full gate: `make check`
