# PYPOST-1232: Dev Docs Verification

## Scope

This is a 1-story-point, test-only assertion fix (`envelope.v == 1` -> `== 2` in
`tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`).
No production behavior changed, so no `doc/dev` content needed to change — but existing docs
were checked for drift, per the step's spirit.

## Checked

- `doc/dev/environment_encryption_at_rest.md` — section "Encrypted export file round-trip
  (PYPOST-1009)" (around line 210-232) already documents the guard as
  `Envelope on disk | Hidden field is v2 Fernet envelope; secret string absent` and references
  the fixed test's node id directly. This doc was already accurate; only the test assertion
  had drifted from it. No edit needed.
- `doc/dev/encryption_key_migration.md` — references to `v1`/`v2` describe the legacy-upgrade
  migration tooling (`encryption_migrate upgrade-v2`), not the export default; still accurate.
- `doc/dev/environments_dialog.md`, `doc/dev/json_export_root.md` — mention
  `tests/test_environment_export.py` only as a coverage reference (node id list), no version
  claims to correct.

## Outcome

No `doc/dev` files required changes. This file records that the check was performed rather
than skipped.
