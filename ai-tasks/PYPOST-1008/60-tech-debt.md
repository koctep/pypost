# PYPOST-1008: Technical Debt Analysis

## Shortcuts Taken

None that compromise the lock. This is test-only verification debt.

- **No production change.** `EnvPresenter._open_env_manager` already passes
  `self._storage.serialize_environment_records` into `EnvironmentDialog`.
  The new invoke test was green against current production (Step 4
  confirmation). User-visible Export behavior is unchanged.
- **Dialog construction is patched.** The test patches
  `pypost.ui.presenters.env_presenter.EnvironmentDialog` so the suite never
  runs a real modal `exec()`. That is intentional isolation, not a crutch:
  the assertion still captures `serialize_export_records` and invokes it
  against `FakeStorageManager`.
- **Identity test kept as a sibling.**
  `test_open_env_manager_passes_storage_serializer_directly` still locks
  bound-method identity via local `FakeStorage`. The new test does not
  replace it; architecture required an invoke lock on the shared fake.
- **User docs not updated here.** No user-facing Export change. Developer
  note that presenter wiring is locked by invoke (not identity only)
  belongs in Step 8 (`doc/dev/environments_dialog.md`).

## Code Quality Issues

- **Presenter constructed inline, not via `_make_presenter`.** Required:
  `_make_presenter` injects file-local `FakeStorage`. DoD names
  `tests.helpers.FakeStorageManager`. Same construction as the PYPOST-1000
  import invoke test. Not worth unifying in this ticket.
- **Two tests cover the same constructor seam.** Identity (`__self__` /
  `__func__`) plus invoke (records from `FakeStorageManager`). Complementary
  by design: identity would still pass a no-op `serialize_environment_records`;
  invoke would still pass a working callable that is not the storage method.
  No merge.
- **Pre-existing flake8 on `tests/test_env_presenter.py`** (E402 after
  `pytestmark`, unused `QApplication`, blank-line E302/E304/E305). Unchanged
  and unrelated to this lock.

None of these are production defects or incomplete DoD.

## Missing Tests

**No blocker for this task's DoD.** Presenter → dialog
`serialize_export_records` is now locked as a working, storage-backed
callable.

**Timeout (confirmed):** `tests/test_env_presenter.py` declares module-level
`pytestmark = pytest.mark.timeout(60)` (GUI/presenter tier). The new
`test_open_env_manager_passes_working_serialize_export_records` inherits
that marker. No global `pytest.ini` timeout is used as a substitute. The
test has no unbounded wait; dialog `exec()` is patched.

Sibling gaps remain tracked elsewhere (do **not** re-ticket here):

- Encrypted-at-rest export → import round-trip
  ([PYPOST-1009](https://pypost.atlassian.net/browse/PYPOST-1009))
- Shared single-vs-list JSON export root helper
  ([PYPOST-1010](https://pypost.atlassian.net/browse/PYPOST-1010); already
  implemented on this branch)
- Export… `QTest.mouseClick` on `ENV_EXPORT_BUTTON` — pre-existing, out of
  scope; method-level widget coverage already exists

No new coverage gap was introduced by this change.

## Performance Concerns

None. The new test is hermetic and sub-second; no production path changed.

## Follow-up Tasks

**None.** This ticket created no new work that still needs a Jira issue.

Do not re-ticket [PYPOST-1009](https://pypost.atlassian.net/browse/PYPOST-1009)
or [PYPOST-1010](https://pypost.atlassian.net/browse/PYPOST-1010). Those are
parent PYPOST-988 siblings, not follow-ups of this wiring lock.

Step 8 of **this** task should note the invoke lock in
`doc/dev/environments_dialog.md` — documentation, not a Debt issue.
