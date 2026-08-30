# PYPOST-1232: Environment export round-trip test still asserts envelope v1 after the v2 default

## Goals

The test suite is the guarantee that CI results can be trusted. When a test's expected value no
longer matches the production behavior it is supposed to verify, the test stops doing its job:
it either passes for the wrong reason (masking what the code actually does) or, if production
behavior regresses back toward the old value, it would pass even though a real regression
occurred. Keeping this test's assertion aligned with the shipped encryption default (PYPOST-1018)
restores its ability to catch future regressions in exported-secret envelope versioning, and keeps
the suite an accurate, trustworthy description of current system behavior for anyone reading it.

## User Stories

- As a developer relying on CI, I want the environment export/import round-trip test to assert the
  envelope version that the encryption codec actually produces today, so a passing test run means
  the export feature genuinely behaves as documented and a future regression in envelope
  versioning would be caught.
- As a developer reading the test suite, I want test assertions to reflect current, shipped
  behavior (not superseded behavior), so the tests remain a reliable reference for how the export
  feature works.

## Definition of Done

- The round-trip export/import test's assertion on the encrypted value envelope's version field
  matches the version produced by the current default encryption codec (the value already shipped
  and locked by `tests/test_default_runtime_encrypt_v2.py`).
- The full test suite passes, including the corrected test and the existing v2-default test.
- No production code behavior changes as part of this task.

## Task Description

`tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
encrypts a hidden environment variable, writes it to an export file, and inspects the resulting
encrypted value envelope. It currently asserts the envelope's version field equals `1`.

Since commit 42c1d98c (PYPOST-1018), `EnvironmentSecretsCodec.VERSION` in
`pypost/core/environment_secrets_codec.py` defaults to the v2 envelope version (`2`), and
`tests/test_default_runtime_encrypt_v2.py` already locks this new default in a dedicated test.
The export round-trip test was not updated at the same time and is now a stale outlier that
asserts a version the export path no longer produces, making that specific assertion fail (or,
depending on exact wiring, pass without meaningfully verifying current behavior).

This task corrects the round-trip test's expectation to match the already-shipped v2 default. It
is a test-only correction with no change to exported/imported data formats, encryption behavior,
or any other production code path. Before changing the assertion, confirm no other test or caller
depends on the export path producing a v1 envelope by default (a legacy `encrypt_v1` path exists
for producing v1 envelopes explicitly and is out of scope here).

**Scope boundaries**:
- In scope: the single assertion (and any directly related setup/assertions in the same test) in
  `tests/test_environment_export.py`.
- Out of scope: any change to `pypost/core/environment_secrets_codec.py` or other production code;
  any change to the explicit `encrypt_v1` / legacy v1 envelope support; any change to import
  behavior for legacy v1-encrypted data (backward-compatible import of v1 envelopes must continue
  to work and is not touched by this task).

## Q&A

- Q: Does any caller or test rely on the export path defaulting to a v1 envelope?
  A: No production caller was found that depends on export defaulting to v1; the only place v1 is
  intentionally produced is via the explicit `encrypt_v1` method, which is unaffected by this
  change. `tests/test_default_runtime_encrypt_v2.py:36` already asserts the v2 default at the
  codec level, confirming v2 is the current, intended default for encryption (including export).
