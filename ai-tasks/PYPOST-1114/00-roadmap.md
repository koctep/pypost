# Roadmap: PYPOST-1114

## Task Metadata

- **Implementation language**: Python (existing `pypost` package; guidance: `lsr-python`)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1114/00-roadmap.md` — created from template; language recorded
  - `ai-tasks/PYPOST-1114/10-requirements.md` — goals, user stories, DoD (AC-1..AC-9), scope,
    entities, Q&A; sources: Jira PYPOST-1114, `ai-tasks/PYPOST-1088/60-tech-debt.md` (TD-2),
    `doc/dev/environment_encryption_at_rest.md` § File-backed registry caching
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1114/20-architecture.md` — chosen: content-digest identity
    (`(path, sha256(bytes))`) inside `MtimeFileCache`; no call-site/API changes; alternatives
    (writer counter, extended stat, hybrid, TTL) compared; Step 3 repro design with `os.utime`
    mtime pinning in `tests/test_pypost_1114_failing_repro.py`
  - Review fix: sourced Research (web search: kernel multigrain-ts docs, FS timestamp resolution,
    utimensat(2)); hash/load race closed by post-load re-hash (cache only if digest unchanged),
    repro test 6 added, residual A→B→A limit recorded in Risks/AC-9 docs
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_pypost_1114_failing_repro.py` — run via
    `make test PYTEST_ARGS="tests/test_pypost_1114_failing_repro.py -p no:randomly -rA"`:
    5 failed / 1 passed on current code (mtime pinned with `os.utime(ns=...)`, pin asserted)
    - 1 `test_generic_cache_same_mtime_same_length_rewrite_reloads` — red: stale `'AAAA'` != `'BBBB'`
    - 2 `test_registry_two_rapid_rewrites_resolve_latest_active_key` — red: stale active key id1
      after first same-mtime rewrite (expected id2)
    - 3 `test_spec_same_mtime_rewrite_reloads` — red: stale spec marker `'one'` != `'two'`
    - 4 `test_unchanged_file_is_not_reparsed` — green (AC-5 guard; must stay green)
    - 5 `test_touch_only_change_is_not_reparsed` — red: loader re-parsed identical bytes, calls=2
    - 6 `test_rewrite_during_load_is_not_cached_then_rollback_reloads` — red: stale `'v2'` != `'v1'`
      after rollback
- [x] **STEP 4: Development**
  - [x] Iteration 1: `pypost/core/key_sources/file_cache.py` — `MtimeFileCache` identity switched
    from `(path, st_mtime_ns)` to `(path, sha256(bytes))` (private `_digest`, never logged or
    returned); hit returns cached value without loader call; miss loads, re-hashes, caches only
    if digest unchanged (else / re-read `OSError` → `clear()` + uncached value); initial-read
    `OSError` or loader `None` → `clear()` + `None`; public API, class name and callers unchanged
  - [x] Gates: repro `tests/test_pypost_1114_failing_repro.py` 6 passed; key-source/encryption
    tests (8 files) 86 passed; `make typecheck` OK; `make lint` OK; `make check` test stage
    1 file failed — `tests/test_pytest_exit_policy.py` worker timeout, also TIMED_OUT at base
    `095b8f70` (pre-existing, unrelated to this change)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1114/40-code-cleanup.md` — cleanup report
  - `tests/test_pypost_1114_failing_repro.py` — module docstring updated (repro now green ->
    regression tests); helper docstrings added; `_registry_json` moved to helpers section; no
    test logic changes; checked by inspection vs `.flake8` (outside `make lint`
    scope, Step 7 tech-debt candidate)
  - `pypost/core/key_sources/file_cache.py` — no changes needed
  - Gates: `make lint` OK; `make typecheck` OK (baseline); targeted `make test` (repro +
    chain_coverage + secret_store) 3/3 files passed
- [x] **STEP 6: Observability**
  - Deviation from `20-architecture.md` ("no new log statements"): accepted in Step 6 review;
    architecture § Security (AC-7) and Risks table amended to match
  - `ai-tasks/PYPOST-1114/50-observability.md`: observability report and decision (no metrics:
    no key-source metrics facility, rare self-healing events, AC-7 label risk)
  - `pypost/core/key_sources/file_cache.py`: 2 DEBUG events, path/reason only:
    `file_cache_rewrite_during_load path=`, `file_cache_recheck_failed path= reason=`; hit and
    normal miss paths stay silent
  - `tests/test_pypost_1114_observability.py`: 3 caplog tests (exact message; no
    content or digest hex/repr in message or args; miss/hit silent)
  - Gates: `make lint` OK; `make typecheck` OK (baseline); targeted `make test` (repro +
    chain_coverage + secret_store + observability) 4/4 files passed
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1114/60-tech-debt.md` — verdict NO BLOCKER; resolves PYPOST-1088 TD-2
  - Follow-ups (Jira to be created): TD-1 Medium lint `tests/` via make; TD-2 Low rename
    `MtimeFileCache` (+ drop `_clear` alias, 2 cache-level tests); TD-3 Low remove 4 redundant
    PYPOST-1088 mid-test `clear_registry_cache()` calls, drop only that name from 2 imports,
    update `doc/dev/encryption_key_migration.md:612-617` (keep conftest autouse fixture)
  - Assessed, no issue: per-lookup read + sha256 / stat pre-filter (profiling-gated); A→B→A,
    torn writes, no thread-safety (accepted limits, Step 8 docs)
  - Pre-existing NON-BLOCKER: `tests/test_pytest_exit_policy.py` (`make test` and
    `make test-cov` fail-closed tests) → PYPOST-1299
  - Timeout markers: both new test files `timeout(30)` — PASS; targeted `make test` 5/5 files
- [x] **STEP 8: Dev Docs**
  - `doc/dev/environment_encryption_at_rest.md` § File-backed registry caching (heading/anchor
    kept): identity `(path, sha256(bytes))`, `get()` flow with post-load re-hash, guarantees
    (rewrite seen by next lookup, touch-only not re-parsed), cost (read + SHA-256 per lookup,
    3 reads on a miss), 2 DEBUG events (path/reason only), limits (A→B→A, torn writes → atomic
    replace, no thread-safety, historical class name → PYPOST-1314); table `_mtime_ns` →
    `_digest`; `clear*()` documented as test isolation only; same-tick race moved to background,
    mid-test clears redundant → PYPOST-1313
  - Same file § Tests: removed same-tick race wording; added PYPOST-1114 regression tests
    (`tests/test_pypost_1114_failing_repro.py`, `tests/test_pypost_1114_observability.py`)
  - `doc/dev/encryption_key_migration.md` § Tests: rotation tests no longer need
    `clear_registry_cache()`; remaining calls redundant, removal tracked in PYPOST-1313
  - grep `doc/` for mtime / `clear_registry_cache` / same-tick: no other stale references
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1114/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1114/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1114/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1114/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1114/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
