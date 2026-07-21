# PYPOST-830: Dev Docs Update

## Summary

Documented the gateway `unittest.TestCase` convention for shared suite `qapp`:
`@pytest.mark.usefixtures("qapp")` instead of module-local `setUpClass`
`QApplication`. Plain pytest modules keep the `qapp` parameter style.

## Changes

- `doc/dev/gui_testing.md` — § Shared `qapp` (two consumers); `usefixtures`
  example for gateway TestCase; consumer list marks gateway + H3 as
  `usefixtures`; worker sibling still on `setUpClass` noted; troubleshooting
  and references include PYPOST-830
- `doc/dev/environment_storage_async.md` — responsiveness harness notes
  gateway `usefixtures("qapp")` (PYPOST-830)
- `doc/dev/testing.md` — GUI section points at shared-`qapp` styles and
  `gui_testing.md` § Shared `qapp`

No user-facing docs (test-harness consistency only).

## Key developer guidance

1. Reuse `tests/conftest.py` `qapp`; never invent a second module-local app.
2. Plain pytest: `def test_...(qapp)`.
3. `unittest.TestCase`: `@pytest.mark.usefixtures("qapp")` on the class.
4. Gateway units + H3 stress follow (3); responsiveness follows (2).

## Validation

- [x] `gui_testing.md` no longer implies `setUpClass` for gateway surface
- [x] Storage async + suite testing docs cross-link the convention
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 7 marked complete
