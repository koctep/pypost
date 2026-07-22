# PYPOST-884: Dev Docs Update

## Summary

Documented that collection storage worker `unittest.TestCase` tests request
shared suite `qapp` via `@pytest.mark.usefixtures("qapp")` (same convention as
gateway units from PYPOST-830). Removed stale notes that the worker module
still used module-local `setUpClass` `QApplication`.

## Changes

- `doc/dev/gui_testing.md` — § Shared `qapp` lists worker under `usefixtures`;
  consumer list updated; references include PYPOST-884
- `doc/dev/environment_storage_async.md` — harness notes cover gateway and
  collection-worker `usefixtures("qapp")` (PYPOST-830 / PYPOST-884)
- `doc/dev/testing.md` — GUI section mentions gateway / collection-worker
  shared-`qapp` styles

No user-facing docs (test-harness consistency only).

## Key developer guidance

1. Reuse `tests/conftest.py` `qapp`; never invent a second module-local app.
2. Plain pytest: `def test_...(qapp)`.
3. `unittest.TestCase`: `@pytest.mark.usefixtures("qapp")` on the class.
4. Gateway units, H3 stress, and collection storage worker follow (3).

## Validation

- [x] `gui_testing.md` no longer marks worker as module-local `setUpClass`
- [x] Storage async + suite testing docs cross-link the convention
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete
