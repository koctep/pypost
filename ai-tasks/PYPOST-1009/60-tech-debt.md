# PYPOST-1009: Technical Debt Analysis

## Shortcuts Taken

None that compromise the lock. This is test-only verification debt.

- **No production change.** Export already writes Hidden values as Fernet
  envelopes via `build_export_payload` /
  `StorageManager.serialize_environment_records`. The new test was green
  against current production (Step 4 confirmation). User-visible Export /
  Import behavior is unchanged.
- **One encrypted scenario.** A single environment (Hidden token + plaintext
  host) locks write-file envelope inspect plus same-key import. List-shape
  JSON and encryption-off round-trip stay on existing tests, as planned.
- **Local encrypted-storage helper.** `_make_encrypted_storage` is file-local
  (temp Fernet key + `PYPOST_ENV_ENCRYPTION_ENABLED` +
  `apply_encryption_settings`). Architecture required this instead of
  `_make_storage`, which deletes those env vars. Not shared with adapter /
  storage tests; those files already inline the same enablement pattern.
- **User docs not updated here.** User Guide already promises encrypted
  export envelopes and same-installation import. Developer note that CI now
  locks that path belongs in Step 8
  (`doc/dev/environment_encryption_at_rest.md`, and
  `doc/dev/environments_dialog.md` if its export test list is updated).

## Code Quality Issues

- **Enablement helper is duplicated across test modules.** Import, adapter,
  and storage tests set the same env vars and call
  `apply_encryption_settings`. A shared fixture would DRY this, but each
  module already has a local pattern and this ticket's helper matches
  architecture. Not worth extracting in this task.
- **Envelope field asserts mirror storage persist tests.** The lock checks
  `EncryptedValueEnvelope.from_payload` plus `enc` / `v` / `alg` / `kid` /
  `ct` on the **export file**, not only `environments.json`. Complementary
  by design; do not merge with persist tests.
- **`secret not in hidden_field.values()` is a weak extra.** The security
  lock is `json.dumps(secret) not in export_text` plus `from_payload`. The
  values check is belt-and-suspenders, not a gap.

None of these are production defects or incomplete DoD.

## Missing Tests

**No blocker for this task's DoD.** Encrypted export → on-disk envelope →
same-machine import is now locked.

**Timeout (confirmed):** `tests/test_environment_export.py` declares
module-level `pytestmark = pytest.mark.timeout(60)` (integration tier).
`test_write_encrypted_export_file_round_trips_through_import` inherits that
marker. No global `pytest.ini` timeout is used as a substitute. The test has
no unbounded wait (no Event.wait, polling loop, or modal `exec()`). Default
signal-based timeout; no `method="thread"`. `cryptography.fernet` is skipped
via `pytest.importorskip` when absent.

Sibling gaps remain tracked elsewhere (do **not** re-ticket here):

- Presenter → dialog export-serializer wiring
  ([PYPOST-1008](https://pypost.atlassian.net/browse/PYPOST-1008))
- Shared single-vs-list JSON export root helper
  ([PYPOST-1010](https://pypost.atlassian.net/browse/PYPOST-1010))
- Export… `QTest.mouseClick` on `ENV_EXPORT_BUTTON` — pre-existing PYPOST-988
  missing test; method-level widget coverage already exists; out of scope

No new coverage gap was introduced by this change. Encrypted list-shape
export is intentionally omitted (DoD: one encrypted round-trip is enough).

## Performance Concerns

None. The new test is hermetic (temp key, `tmp_path`, no network or
keyring) and sub-second in the targeted run (12 passed in 0.02s). No
production path changed.

## Follow-up Tasks

**None.** This ticket created no new work that still needs a Jira issue.

Do not re-ticket [PYPOST-1008](https://pypost.atlassian.net/browse/PYPOST-1008)
or [PYPOST-1010](https://pypost.atlassian.net/browse/PYPOST-1010). Those are
parent PYPOST-988 siblings, not follow-ups of this encrypted-file lock.

Step 8 of **this** task should note the encrypted export round-trip lock in
`doc/dev/environment_encryption_at_rest.md` — documentation, not a Debt
issue.
