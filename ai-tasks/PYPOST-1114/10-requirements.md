# PYPOST-1114: Structurally harden MtimeFileCache against same-tick rewrite races

## Goals

PyPost resolves environment-encryption keys from operator-managed JSON files: the env-channel key
registry (`PYPOST_ENV_ENCRYPTION_KEYS_FILE`) and the secret-store spec
(`PYPOST_ENV_ENCRYPTION_SECRETS_FILE`). Both are cached in-process by the shared file cache
(`MtimeFileCache`), which decides "has this file changed?" from the file's modification timestamp
only.

When the same file is rewritten twice within one filesystem timestamp tick, the timestamp does not
change and PyPost keeps serving the **previous** file contents. For key rotation this means the
application can keep encrypting with, or resolving, a key the operator has already replaced. In
the test suite it produced the order-dependent flakes fixed in PYPOST-1088.

PYPOST-1088 fixed the symptom by adding an explicit cache-clear call at the 4 known places that
rewrite the registry mid-test. That relies on every current and future caller (tests, scripts,
admin tooling) remembering a hidden obligation; forgetting it silently brings back the same flaky,
stale-key behaviour.

Business goal: **a rewrite of a key registry or secret-store spec file is always observed by the
next key lookup, regardless of timestamp resolution and without any caller-side cache-clear
obligation**, so key rotation is reliable and the PYPOST-1088 class of flakes cannot recur.

## User Stories

- As an **operator rotating encryption keys**, I want PyPost to pick up the new active key from the
  registry file on the next lookup, even if I (or my tooling) rewrote the file twice in quick
  succession, so that data is never encrypted with a key I have just retired.
- As a **developer writing a test or script** that rewrites a registry/spec file mid-run, I want
  the next key resolution to see the new contents without calling any cache-clear function, so I
  cannot accidentally write a flaky test.
- As a **maintainer**, I want an automated regression test that reproduces the original
  same-tick double-rewrite scenario with no manual cache clear, so the fix is proven structurally
  and protected against regressions.

## Definition of Done

- **AC-1 (registry, same tick):** Given the env-channel registry file has been read once, when it
  is rewritten with different contents (e.g. a different `active_key_id`) such that its
  modification timestamp is identical to the previous version, then the next key resolution
  (`try_resolve_active` / `try_resolve_by_id`) returns results based on the **new** contents —
  with no call to `clear_registry_cache()` or any other cache-clear function.
- **AC-2 (secret-store spec, same tick):** The same guarantee as AC-1 holds for the secret-store
  spec file, without calling `clear_spec_cache()`.
- **AC-3 (generic cache):** The shared file cache itself returns freshly loaded content after a
  same-timestamp rewrite of its file, including when the old and new contents have the same byte
  length. Any future user of the shared cache inherits the guarantee automatically.
- **AC-4 (two rapid rewrites):** A regression test performs two back-to-back rewrites of the
  registry file (rotation scenario from PYPOST-1088), with no manual cache clear, and asserts the
  resolved active key matches the second write. The test is deterministic: it forces the
  same-timestamp condition rather than relying on timing luck, and it fails against the current
  (pre-fix) code.
- **AC-5 (performance preserved):** Repeated lookups against an **unchanged** file do not re-run
  the file's parse/validation step (verified by a loader-call-count assertion, as in the existing
  `test_mtime_file_cache_clear`).
- **AC-6 (existing behaviour preserved):** Missing, unreadable, deleted, invalid-JSON and non-object
  JSON files keep their current outcome (lookup yields no registry/spec; no exception). A change of
  configured path is still detected. Existing public entry points `MtimeFileCache.clear()`,
  `clear_registry_cache()` and `clear_spec_cache()` remain available and keep working (they are
  still used by `tests/conftest.py` and the 4 PYPOST-1088 call sites).
- **AC-7 (no secret leakage):** Change detection does not log, persist, or expose key material or
  any value derived from file contents beyond what is logged today.
- **AC-8 (quality gates):** `make check` passes; `make typecheck` shows no regression against
  `mypy-baseline.json`; every new/changed test declares a pytest timeout (module `pytestmark` or
  per-test marker).
- **AC-9 (docs):** `doc/dev/environment_encryption_at_rest.md` (§ File-backed registry caching) and
  the related note in `doc/dev/encryption_key_migration.md` no longer state that callers must call
  a cache-clear function after a mid-run rewrite; they describe the new guarantee and its limits.

## Task Description

### Current behaviour (observed in code)

- `pypost/core/key_sources/file_cache.py` — `MtimeFileCache.get(path, loader)` returns the cached
  value when the path string and `st_mtime_ns` both match the previous read; otherwise it calls
  `loader`. A stat failure or `None` from the loader clears the cache.
- Two module-level instances share this logic:
  - `_registry_cache` in `pypost/core/key_sources/env.py` (used by `EnvKeySource`, cleared by
    `clear_registry_cache()`);
  - `_spec_cache` in `pypost/core/key_sources/secret_store.py` (used by `SecretStoreKeySource`,
    cleared by `clear_spec_cache()`).
- Explicit clears exist in `tests/conftest.py` (autouse, before/after each test — between-test
  isolation only) and after mid-test rewrites in `tests/test_encryption_migration.py` (1) and
  `tests/test_encryption_migrate_cli.py` (3) — the 4 PYPOST-1088 point fixes.
- PyPost itself never writes these files; they are written by external actors (operators,
  deployment tooling, tests, scripts).

### Scope

In scope:

- Making change detection of the shared file cache robust to same-timestamp rewrites, so both
  current users (env registry, secret-store spec) benefit without caller changes.
- Deterministic regression test(s) per AC-1..AC-5.
- Developer documentation update per AC-9.

Out of scope:

- Removing the 4 PYPOST-1088 explicit `clear_registry_cache()` calls or the autouse conftest
  fixture (they stay as harmless isolation; removing them is optional and not required for DoD).
- Thread-safety / concurrent-access guarantees of the cache (not provided today; unchanged).
- Detecting a rewrite that happens **during** a single read (torn/partial writes) — atomic file
  replacement remains the writer's responsibility.
- Other file caches or file-based stores in PyPost (config, history, library) that do not use
  `MtimeFileCache`.
- Choosing the mechanism (write-generation counter, content hash, additional file metadata, etc.)
  — deferred to Step 2 (Architecture).

### Non-functional requirements

- **Correctness over timestamp resolution:** freshness must not depend on filesystem timestamp
  granularity (coarse-granularity filesystems, fast successive writes).
- **Performance:** registry/spec files are small (KB range); a small bounded per-lookup cost to
  detect changes is acceptable, but the full parse/validate step must run only when the file
  actually changed (AC-5).
- **Security:** no key material or content-derived identifiers in logs (AC-7).
- **Compatibility:** no change to public function names/signatures used by tests and docs; no new
  runtime dependency.

### Constraints and assumptions

- Implementation language: Python, within the existing `pypost` package.
- Tooling is make-only (`make test`, `make check`, `make typecheck`); no direct pytest/flake8/mypy.
- Because file writers are external to PyPost, the guarantee must hold for writes PyPost does not
  perform or observe (assumption carried into Step 2: a writer-side hook alone cannot satisfy
  AC-1/AC-2).

## Main Entities

| Entity | Business meaning | Key attributes |
| --- | --- | --- |
| Key registry file | Operator-managed list of encryption keys for the env channel | path, active key id, key id → material map |
| Secret-store spec file | Operator-managed description of where key material lives | path, backend config |
| File cache | In-process memory of the last parsed version of one file | identity of the cached file version, parsed value |
| Writer | Any external actor rewriting a file (operator, tooling, test, script) | not under PyPost control |
| Key lookup | `EnvKeySource` / `SecretStoreKeySource` resolution of active or historical key | must reflect the latest file version |

## Q&A

- **Q: Why not just keep the explicit `clear_registry_cache()` calls?** A: They are a hidden,
  unenforced caller obligation; any new test/script with the same shape reintroduces the
  PYPOST-1088 flake, and production operators rotating keys have no such hook at all.
  (Source: `ai-tasks/PYPOST-1088/60-tech-debt.md` TD-2.)
- **Q: Must the fix cover the secret-store spec cache too?** A: Yes — both are instances of the same
  `MtimeFileCache` and share the defect; fixing the shared cache satisfies both (AC-2, AC-3).
- **Q: Jira suggests a writer-side generation counter or a content hash. Which one?** A: Mechanism
  is an architecture decision (Step 2). Requirement-level constraint only: writers are external to
  PyPost, so the solution must detect changes PyPost did not make.
- **Q: Must the 4 PYPOST-1088 call sites be reverted?** A: No. The new regression test (AC-4) is
  the proof that the guarantee holds without them; leaving them in place is acceptable.
- **Q: Are partially-written files in scope?** A: No — out of scope; behaviour for invalid JSON is
  unchanged (AC-6).
