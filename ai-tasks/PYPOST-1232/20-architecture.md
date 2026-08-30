# PYPOST-1232: Environment export round-trip test still asserts envelope v1 after the v2 default

## Research

- Confirmed root cause: `pypost/core/environment_secrets_codec.py` defines
  `EnvironmentSecretsCodec.VERSION: ClassVar[int] = 2` (line 37) and
  `EncryptedValueEnvelope.from_payload` validates incoming payloads against `cls.VERSION` (line 47).
  This default was shipped in commit `42c1d98c` (PYPOST-1018).
- `tests/test_default_runtime_encrypt_v2.py:36` already locks the v2 default at the codec level:
  `test_codec_encrypt_defaults_to_v2` asserts `envelope.v == 2` and
  `EnvironmentSecretsCodec.VERSION == 2`.
- `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
  (assertion at line 141: `assert envelope.v == 1`) was not updated when the v2 default shipped. It
  now asserts a version the export path no longer produces — a stale assertion, not a production
  defect.
- Per the requirements Q&A, no production caller or other test depends on the export path
  defaulting to a v1 envelope. The only intentional v1 producer is the explicit `encrypt_v1`
  method, which is out of scope and untouched. Legacy v1 import compatibility is likewise
  untouched.
- Conclusion: this is a single stale test assertion in `tests/test_environment_export.py`. No
  production code investigation turned up any other place that needs to change.

## Implementation Plan

Step 4 will change exactly one line in `tests/test_environment_export.py`, in
`test_write_encrypted_export_file_round_trips_through_import`:

- `assert envelope.v == 1` → `assert envelope.v == 2`

No other lines in that test, and no other test, need to change: the surrounding assertions
(`envelope.enc is True`, `envelope.alg == "fernet"`, `kid`/`ct` types, secret redaction, and the
subsequent import round-trip) are version-agnostic and already correct.

**Mandatory — Failing Repro (next Step 3):** The existing test node
`tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
already contains, at line 141, the assertion `assert envelope.v == 1`, which fails today because
the export path (via `EnvironmentSecretsCodec`, defaulting to `VERSION = 2`) produces a v2
envelope. This pre-existing failing assertion *is* the red repro: it already encodes the "wrong
version literal" defect described by this task, so Step 3 does not need to author a new test.
Step 3's job is to run this test node, confirm it currently fails (red) specifically on the `v == 1`
assertion (not on some unrelated error), and record that failing run as the baseline repro. Step 4
then edits the single literal (`1` → `2`) to make the node pass (green), per the plan above. No
live external dependencies are involved (encryption uses an in-memory/mocked key provider per the
existing fixture in that test module), so the repro is fully reproducible via `make test` /
`pytest tests/test_environment_export.py -k test_write_encrypted_export_file_round_trips_through_import`.

## Architecture

This is a test-only change. There are no module, component, or interface changes:

- No production code in `pypost/` is modified.
- No new modules, dependencies, or interfaces are introduced.
- The change is confined to one assertion literal inside one existing test function in
  `tests/test_environment_export.py`.
- System behavior (encryption, export, import, envelope versioning) is unchanged; only the test's
  expected value is corrected to match already-shipped behavior.

## Q&A

- Q: Does any caller or test rely on the export path defaulting to a v1 envelope?
  A: No. Confirmed in `10-requirements.md` Q&A — the only intentional v1 producer is the explicit
  `encrypt_v1` method (out of scope), and `tests/test_default_runtime_encrypt_v2.py:36` already
  locks v2 as the current default at the codec level.
