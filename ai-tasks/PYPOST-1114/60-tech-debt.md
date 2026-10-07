# PYPOST-1114: Technical Debt Analysis

**Verdict:** NO BLOCKER. The structural fix is a single-file change
(`pypost/core/key_sources/file_cache.py`): cache identity moved from `(path, st_mtime_ns)` to
`(path, sha256(bytes))`, with a post-load re-hash and two DEBUG events (Step 6). Public API,
loader contract and call sites are unchanged. Both new test files declare a module-level pytest
timeout. The remaining debt is naming, tooling scope, now-redundant test scaffolding, and
accepted design limits. One pre-existing failing test is already tracked
([PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299)).

**Resolves PYPOST-1088 TD-2.** `ai-tasks/PYPOST-1088/60-tech-debt.md` TD-2 asked for a structural
fix to `MtimeFileCache` so that callers no longer need to remember a `clear()` call, plus a
regression test that reproduces the race without one. Both are done here:

- content-digest identity in `MtimeFileCache`;
- `tests/test_pypost_1114_failing_repro.py::test_registry_two_rapid_rewrites_resolve_latest_active_key`
  (two pinned-mtime rewrites, no manual clear).

PYPOST-1088 files are not edited.

Scope reviewed:

- `git diff pypost/core/key_sources/file_cache.py`
- `tests/test_pypost_1114_failing_repro.py` (new)
- `tests/test_pypost_1114_observability.py` (new)
- cache users: `pypost/core/key_sources/env.py`, `pypost/core/key_sources/secret_store.py`
- explicit clears: `tests/conftest.py`, `tests/test_encryption_migration.py`,
  `tests/test_encryption_migrate_cli.py`, `tests/test_key_sources_chain_coverage.py`
- `Makefile` (`lint` target)
- `ai-tasks/PYPOST-1114/{00,10,20,40,50}-*.md`

---

## Shortcuts Taken

- **PYPOST-1088 point-fix clears left in place (Priority: Low).** The 4 mid-test
  `clear_registry_cache()` calls are now redundant for correctness:
  - `tests/test_encryption_migrate_cli.py:144`, `:201`, `:557`
  - `tests/test_encryption_migration.py:299`

  Their imports also need trimming: drop only the `clear_registry_cache` name from
  `from pypost.core.key_sources.env import EnvKeySource, clear_registry_cache`
  (`tests/test_encryption_migrate_cli.py:9`, `tests/test_encryption_migration.py:15`);
  `EnvKeySource` is still used. The dev-doc paragraph in
  `doc/dev/encryption_key_migration.md:612-617` still says these tests call
  `clear_registry_cache()`, so it must change with them.

  The same-mtime rewrite they worked around is now detected by content. They were explicitly
  kept (`10-requirements.md` Out of Scope; `20-architecture.md` Q&A). They do no harm, but they
  suggest to readers that a manual clear is still required after a rewrite. That is the hidden
  caller obligation this task removes. The repro test proves the guarantee without them.
  **Decision:** remove them in a follow-up. Keep the conftest fixture (see the next item).
- **Autouse `_reset_key_source_caches` fixture in `tests/conftest.py` (Priority: Low,
  merged into the item above).** For same-tick freshness this fixture is no longer needed.
  It still does one legitimate job: between tests it isolates the two module-level singletons,
  so a value loaded by one test's monkeypatched loader cannot be served to the next test. It
  costs two attribute resets per test. **Decision:** keep it. The follow-up should only update
  its docstring to say it provides between-test isolation and does not work around staleness.
  This also closes the open "Suite-wide autouse fixture" note in PYPOST-1088 § Shortcuts Taken
  as "keep, by design".
- **Deviation from architecture: two DEBUG events added in Step 6 (Priority: none, closed).**
  `20-architecture.md` § Security originally said "no new log statements". It was amended in
  Step 6, and the change was accepted in review. AC-7 is covered by caplog tests. This is not
  debt.
- **No hardcoded values or temporary workarounds** in production code. SHA-256 is a fixed
  algorithm choice, documented in `20-architecture.md` § Security.

---

## Code Quality Issues

- **The class name `MtimeFileCache` is now misleading (Priority: Low).** Identity is
  content-based and mtime is no longer read at all. Only the class docstring explains this ("The
  class name is historical"). Rename candidates: `ContentDigestFileCache` or `FileContentCache`.
  Blast radius:
  - 2 production imports and annotations (`env.py:9,15`, `secret_store.py:12,23`);
  - 2 test modules (`test_key_sources_chain_coverage.py`, `test_pypost_1114_failing_repro.py`)
    and the test name `test_mtime_file_cache_clear`;
  - the dev-doc heading and its anchor `#file-backed-registry-caching-mtimefilecache`, which
    `doc/dev/encryption_key_migration.md:616` links to.

  It is a mechanical change, but the docs and anchor must move with it, and a deprecated
  `MtimeFileCache = <NewName>` alias should be kept for one release. **Decision:** keep this as a
  follow-up, not done here. It was out of scope by design (`20-architecture.md` § Interfaces and
  Risks).
- **`MtimeFileCache._clear()` is a trivial alias of `clear()` (Priority: Low, merged into the
  rename above).** This predates the task (PYPOST-1088 § Code Quality Issues, never ticketed).
  It was left as-is in Step 5 because it was out of scope. The rename touches the same class, so
  it should inline `self.clear()` at the 4 internal call sites in `get()` and delete `_clear()`.
- **Tests depend on private names (Priority: Low, informational, no follow-up).**
  - `test_spec_same_mtime_rewrite_reloads` calls `SecretStoreKeySource._load_spec()`.
  - `test_recheck_failure_logs_path_and_reason_only` monkeypatches
    `file_cache._digest_file`.

  If either private name is renamed, these tests fail with an `AttributeError` instead of a
  meaningful assertion. Repo tests already use this pattern (see PYPOST-1088 § Code Quality
  Issues), and it is the least invasive way to inject the second-read failure. Not actionable on
  its own.

---

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Same-mtime, same-length rewrite reloads (AC-3) | Present (`test_generic_cache_same_mtime_same_length_rewrite_reloads`) |
| Two rapid registry rewrites, no manual clear (AC-1, AC-4) | Present (`test_registry_two_rapid_rewrites_resolve_latest_active_key`) |
| Same-mtime spec rewrite (AC-2) | Present (`test_spec_same_mtime_rewrite_reloads`) |
| Unchanged file is not re-parsed (AC-5) | Present (`test_unchanged_file_is_not_reparsed`, `test_mtime_file_cache_clear`) |
| Touch-only change does not re-parse (design semantics) | Present (`test_touch_only_change_is_not_reparsed`) |
| Rewrite during load is not cached; rollback reloads | Present (`test_rewrite_during_load_is_not_cached_then_rollback_reloads`) |
| DEBUG events carry path/reason only; hit/miss silent (AC-7) | Present (`tests/test_pypost_1114_observability.py`, 3 tests) |
| Cache level: file deleted after a cached load → `get()` returns `None` and clears; recreated file reloads | Missing. The behaviour carried over unchanged (initial-read `OSError` → clear + `None`), but no test calls `MtimeFileCache` directly for it. Callers' `is_file()` pre-check hides it in the integration tests. Low; merged into the rename follow-up |
| Cache level: same content at a different path reloads (path is part of identity, AC-6) | Missing. The `_path` comparison was kept but has no direct test. Low; merged into the rename follow-up |
| A→B→A rewrite completed inside one loader call | Not testable by design (accepted limit, see Performance Concerns / limits) |

**Timeout marker review: NO BLOCKER.** Both new files declare
`pytestmark = pytest.mark.timeout(30)` at module level:

- `tests/test_pypost_1114_failing_repro.py`
- `tests/test_pypost_1114_observability.py`

No other test file was changed by this task.

**Lint coverage gap for tests (Priority: Medium).** In `make lint`, flake8 covers only
`pypost/` (`flake8 --jobs=1 pypost/`, `Makefile:214`). The other two `lint` commands
(`Makefile:215-216`) are the doc checks `scripts/lint_user_docs.py` and
`scripts/check_user_docs_links.py`. So no make target runs flake8 on `tests/`, including both
new test files. Steps 5 and 6 could only check them by eye against `.flake8`,
because AGENTS.md forbids calling flake8 directly. This is not caused by this task; the gap
covers all of `tests/`. It matters because every task adds tests that no lint gate checks.
Turning flake8 on for `tests/` may surface existing violations, so the follow-up probably needs a
cleanup pass, or a per-file ignore baseline, before `make lint` / `make check` can include it.

---

## Performance Concerns

- **Read + SHA-256 on every lookup, including cache hits (Priority: Low, no follow-up for
  now).** A hit now costs one `read_bytes()` and one `sha256` instead of one `stat()`. A miss
  costs three reads: the digest read, the loader's own `open` + `json.load`, and the post-load
  re-hash. Callers also do an `is_file()` stat first. Registry and spec files are KB-sized and are
  read on key lookups, not in tight loops. The non-functional requirements allow this bounded
  cost, and the expensive parse/validate step still runs only when the content changes (AC-5).
  - **Possible optimisation (arch option D):** a stat pre-filter. When `(mtime_ns, size, ino)`
    changed, skip the hash and reload directly. When it is unchanged, hash as today. This saves
    the hash only on the miss path. A hit must still hash, or same-tick freshness is lost.
  - **Decision:** act only if profiling shows key lookups on a hot path. No issue now, because
    there is no evidence of cost, and a ticket without a trigger would be speculative.
  - **Related:** `read_bytes()` has no size bound. Before this change, a very large file at the
    configured path was read only on a miss; now it is read on every lookup. The path is
    operator-controlled config, so this is noted only.
- **Accepted design limits (Priority: Low, no follow-up). Record them in the Step 8 docs
  (AC-9).**
  - **A→B→A inside one loader call:** a writer changes the file to B before the loader reads it,
    then back to A before the re-hash. The value of B is cached under the digest of A until the
    next real content change. No before/after content check can detect this. It needs two
    external writes inside a parse window of a few ms, and it corrects itself on the next real
    change. Accepted in `20-architecture.md` § Risks.
  - **Torn or partial writes:** out of scope (`10-requirements.md`). Writers must replace the
    file atomically. A torn read gives invalid JSON, so the loader returns `None` and no lookup
    result is produced. Behaviour is unchanged.
  - **No thread-safety:** `get()` updates `_path`, `_digest` and `_value` in separate
    assignments. A concurrent reader could see a new digest paired with the old value for one
    call. This was already true of the mtime design, and thread-safety is out of scope. Revisit
    only if key sources start being resolved from several threads at once.
- **Existing dev docs still describe the old mtime mechanism (Step 8 input, AC-9).** These
  lines in `doc/dev/environment_encryption_at_rest.md` are now wrong and must be rewritten in
  Step 8, together with the limits above:
  - `:97` — `get()` re-parses when `st_mtime_ns` changes;
  - `:105` — `MtimeFileCache.clear()` clears an `_mtime_ns` attribute (now `_digest`);
  - `:117` — the same-tick `st_mtime_ns` stale-cache race is described as current behaviour.

---

## Follow-up Tasks

### TD-1 — Medium: lint `tests/` through a make target

- **Item:** Extend `make lint` (or add a `lint-tests` target that `make check` runs) so that
  flake8 also checks `tests/`. Clean up existing violations first, or add a narrowly scoped
  per-file-ignores baseline, so the gate starts green.
- **Notes:** AGENTS.md is make-only, and flake8 in `make lint` covers only `pypost/`, so new
  test files are never linted today. Steps 5 and 6 of
  this task had to check by eye. This affects all of `tests/`, not just this task.
- **Jira:** [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) (existing issue, linked
  instead of creating a duplicate)

### TD-2 — Low: rename `MtimeFileCache` to reflect content identity

- **Item:** Rename `MtimeFileCache` (suggested: `ContentDigestFileCache`) and keep a
  deprecated alias for one release. Update `env.py`, `secret_store.py`, the tests
  (`test_mtime_file_cache_clear` → a matching name) and the dev-doc heading, anchor and the link
  in `doc/dev/encryption_key_migration.md`. In the same change, delete the `_clear()` alias, and
  add the two missing cache-level tests: delete then recreate (`OSError` → `None` → reload), and
  same content at a different path reloads.
- **Notes:** This is maintainer clarity only, with no behaviour change. It was deliberately out of
  scope here (`20-architecture.md` § Interfaces).
- **Jira:** [PYPOST-1314](https://pypost.atlassian.net/browse/PYPOST-1314)

### TD-3 — Low: remove redundant PYPOST-1088 mid-test cache clears

- **Item:** Delete the 4 `clear_registry_cache()` calls:
  - `tests/test_encryption_migrate_cli.py:144`, `:201`, `:557`
  - `tests/test_encryption_migration.py:299`

  In the imports, drop only the `clear_registry_cache` name from
  `from pypost.core.key_sources.env import EnvKeySource, clear_registry_cache`
  (`tests/test_encryption_migrate_cli.py:9`, `tests/test_encryption_migration.py:15`).
  `EnvKeySource` is still used and stays.

  Update `doc/dev/encryption_key_migration.md:612-617`. That paragraph says these tests call
  `clear_registry_cache()` after the rewrite to avoid a same-tick stale read. Step 8 of this task
  rewords it to say the calls are redundant; TD-3 must remove the remaining reference once the
  calls are deleted.

  Confirm the affected tests stay green under repeated runs. Keep the autouse
  `_reset_key_source_caches` fixture, and change its docstring to say it provides between-test
  isolation.
- **Notes:** These calls are redundant now that the cache identity is content-based. Leaving them
  in suggests to readers that a manual clear is still required. They were explicitly out of
  scope (`10-requirements.md`).
- **Jira:** [PYPOST-1313](https://pypost.atlassian.net/browse/PYPOST-1313)

### Assessed, no follow-up issue

- **Per-lookup read + hash and stat pre-filter (option D):** Low. Open an issue only if profiling
  shows cost (see Performance Concerns).
- **A→B→A residual, torn writes, no thread-safety:** Low. These are accepted limits, documented in
  Step 8 (AC-9).
- **Tests depend on private names:** informational; follows existing repo convention.

### NON-BLOCKER — pre-existing

- **Node IDs:**
  - `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
  - `tests/test_pytest_exit_policy.py::test_make_test_cov_fails_closed_when_parallel_runner_is_missing`

  The whole file also hits the 120 s worker timeout.
- **Verdict:** `NON-BLOCKER — pre-existing`. Both fail or time out at base commit `095b8f70`
  without this task's diff (seen in Steps 4 and 5). It has nothing to do with
  `MtimeFileCache`.
- **Jira:** [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299)

---

## Test Results (this step)

`make test PYTEST_ARGS="tests/test_pypost_1114_failing_repro.py tests/test_pypost_1114_observability.py tests/test_key_sources_chain_coverage.py tests/test_encryption_migration.py tests/test_encryption_migrate_cli.py -p no:randomly -q"`:
5/5 files passed, 0 failed (wall-clock 3.33 s). No code was changed in this step.

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| Pytest timeouts | Explicit timeout on all added or changed tests | PASS | Both new files: `pytest.mark.timeout(30)` |
| Targeted tests | Repro, observability and key-source/encryption tests green | PASS | 5/5 files |
| Pre-existing failures | Filed | NON-BLOCKER | PYPOST-1299 |
| Static analysis | `make lint` clean | PASS | `pypost/` only; tests gap is TD-1 |
| Architecture and DoD | Matches the approved architecture | PASS | Step 6 logging deviation amended and accepted |
| Security (AC-7) | No content or digest in logs | PASS | caplog tests |
| **Verdict** | Step 7 gate | **NO BLOCKER — proceed to Step 8** | 3 follow-ups (TD-1 Medium, TD-2/TD-3 Low) to be ticketed |
