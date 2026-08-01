# PYPOST-947: Code Cleanup

## Scope

Step 4 added optional `delay: int = -1` to module and session `ui_fill` and
one fixture smoke test with `unittest.mock.patch` on `QTest.keyClicks`.

## Checklist

- [x] Minimal diff — single kwarg + one forward call + session pass-through
- [x] Docstring updated on module `ui_fill` for delay semantics
- [x] Import order — `unittest.mock` grouped with stdlib in test module
- [x] No unused imports or dead branches
- [x] Types: `delay: int = -1` on both APIs
- [x] Line length ≤ 100

## Verification

```bash
make test PYTEST_ARGS='tests/test_ui_actions.py -v'
```

Result: 32 passed (including `test_ui_fill_via_key_clicks_forwards_delay_kwarg`).

## Notes

- `delay` ignored on setter path — no branch duplication.
- Mock-based smoke avoids slow positive-delay timing asserts in CI.
