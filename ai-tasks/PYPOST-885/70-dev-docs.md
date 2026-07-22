# PYPOST-885: Dev Docs Update

## Summary

Documented that collection/environment gateway and H3 stress tests request
shared suite `qapp` as a free-function parameter (same convention as
responsiveness). Removed stale notes that these modules still used
`unittest.TestCase` + `@pytest.mark.usefixtures("qapp")`.

## Changes

- `doc/dev/gui_testing.md` — § Shared `qapp` lists gateways/H3 under fixture
  parameter style; added free-function example + style guard reference
  (PYPOST-885); process_until consumer list updated
- `doc/dev/environment_storage_async.md` — harness notes cover gateway free
  functions + `qapp` (PYPOST-885) vs worker/presenter `usefixtures`
- `doc/dev/testing.md` — GUI section mentions gateway free-function style and
  `tests/test_gateway_qapp_free_function_style.py`

No user-facing docs (test-harness consistency only).

## Key developer guidance

1. Reuse `tests/conftest.py` `qapp`; never invent a second module-local app.
2. Plain pytest (preferred for gateways/H3/responsiveness): `def test_...(qapp)`.
3. `unittest.TestCase`: `@pytest.mark.usefixtures("qapp")` on the class.
4. Gateway units and H3 stress follow (2) after PYPOST-885.

## Validation

- [x] `gui_testing.md` lists gateways/H3 under free-function `qapp`
- [x] Storage async + suite testing docs cross-link the convention
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete
