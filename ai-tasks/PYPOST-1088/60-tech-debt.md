# PYPOST-1088: Technical Debt Analysis

**Verdict:** Both documented root causes are fixed and independently re-confirmed in this
step. Production changes are three small, additive helper functions
(`MtimeFileCache.clear()`, `clear_registry_cache()`, `clear_spec_cache()`) plus one incidental
defensive guard in `secret_store.py`; no algorithm, schema, or public API was redesigned. No
BLOCKER found. The 4 originally-named node ids passed in every one of 8 repro runs against the
current working tree (see Test Results). One **unrelated** pre-existing flaky test was newly
discovered while stress-running the repro command and is recorded below as
NON-BLOCKER — pre-existing, with baseline evidence.

Scope reviewed (all 9 files this task's diff touches):
`pypost/core/key_sources/env.py`, `pypost/core/key_sources/file_cache.py`,
`pypost/core/key_sources/secret_store.py`, `tests/conftest.py`,
`tests/test_encryption_migrate_cli.py`, `tests/test_encryption_migration.py`,
`tests/test_key_sources_chain_coverage.py`, `tests/test_mcp_server_manager.py`,
`tests/test_metrics_server_startup.py`. `ai-tasks/PYPOST-1088/{10,20,40,50}-*.md` read for
context; `ai-tasks/PYPOST-1054/60-tech-debt.md` (origin story) read for the exact node ids and
prior triage.

---

## Shortcuts Taken

- **Point-fix via manual cache invalidation, not a structural fix to `MtimeFileCache` itself
  (Priority: Medium).** The actual defect (root cause 2A: two registry-file rewrites inside the
  same filesystem timestamp tick produce an unchanged `st_mtime_ns`, so `MtimeFileCache.get()`
  returns the stale value) is fixed by having each affected test call the new
  `clear_registry_cache()` right after rewriting `keys.json`
  (`tests/test_encryption_migrate_cli.py` x3, `tests/test_encryption_migration.py` x1). The
  cache class itself is unchanged and remains just as vulnerable to a same-tick collision as
  before — any *future* test (or an admin/automation script that rewrites the registry file
  twice in quick succession) that forgets the explicit `clear_registry_cache()` call can
  reintroduce the identical stale-read bug. A structural fix (e.g. an internal write-generation
  counter bumped by the writer, or switching the comparison to file content hash instead of
  mtime) would remove the "remember to call clear()" burden entirely; deferred here since it was
  out of this task's declared scope (see `10-requirements.md` Out of Scope: "Modifying encryption
  algorithms, key formats, or on-disk storage schemas beyond test reliability requirements").
- **`os.utime` backdating hack for root cause 2B (Priority: Low).**
  `test_bulk_re_encrypt_does_not_skip_with_plaintext_hidden` now backdates the environments
  file's mtime by 10 seconds (`os.utime(path, (before_mtime - 10, before_mtime - 10))`) purely so
  the subsequent `st_mtime > before_mtime` assertion is guaranteed true on fast filesystems. This
  fixes the specific test but is a workaround for `st_mtime`'s coarse (often 1-second) resolution
  rather than switching the assertion to the nanosecond-resolution `st_mtime_ns` that
  `MtimeFileCache` itself already relies on internally — the two live inconsistently side by side
  now (production cache path: nanosecond comparison; this one test's assertion: second-resolution
  `st_mtime` plus a manual 10s backdate).
- **Incidental, undocumented hardening in `secret_store.py` (Priority: Low).**
  `SecretStoreKeySource._read_spec_file` (`pypost/core/key_sources/secret_store.py:195-202`)
  picked up a new `isinstance(data, dict)` guard as part of this task's diff, returning `None`
  instead of propagating a malformed (non-object) JSON spec file further. This wasn't called out
  in `20-architecture.md`, `40-code-cleanup.md`, or `50-observability.md`, has no accompanying
  test, and — as detailed in Code Quality Issues below — was not mirrored onto the structurally
  identical `EnvKeySource._read_registry_file` loader, so the codebase now has two sibling JSON
  loaders with different defensive postures.
- **Suite-wide autouse fixture for a narrow need (Priority: Low).** `_reset_key_source_caches` in
  `tests/conftest.py` is `autouse=True` at conftest scope, so it runs before/after *every* test in
  the whole repository (thousands of tests), even though only the encryption-migration/key-source
  test modules actually need the reset. Cheap (two attribute-reset calls), but a blunt instrument
  for a narrowly-scoped problem; scoping it to the affected test modules (e.g. via a local
  `conftest.py` under a subdirectory, or explicit fixture use) was not attempted.

---

## Code Quality Issues

- **`env.py` vs `secret_store.py` loader asymmetry (Priority: Medium — latent bug, newly
  inconsistent).** `EnvKeySource._read_registry_file` (`pypost/core/key_sources/env.py:33-49`)
  does `data = json.load(handle)` then immediately `data.get("active_key_id", "")` with no
  type check, catching only `(OSError, json.JSONDecodeError)`. If
  `PYPOST_ENV_ENCRYPTION_KEYS_FILE` ever points at syntactically-valid JSON that isn't an object
  (e.g. `[]`, `"x"`, `42`), this raises an uncaught `AttributeError` instead of returning `None`.
  This bug pre-dates PYPOST-1088 and is out of this task's declared scope, but this task's diff
  added the matching `isinstance(data, dict) else None` guard to the sibling
  `SecretStoreKeySource._read_spec_file` (same `MtimeFileCache`-backed pattern) without adding the
  equivalent guard to `env.py`. The two loaders now diverge in robustness for what is otherwise
  the same read shape. Recommend mirroring the guard onto `env.py::_read_registry_file` (return
  `None` when `data` isn't a `dict`, before the `.get()` calls) in a follow-up.
- **`MtimeFileCache._clear()` is now a redundant one-line wrapper (Priority: Low).**
  `pypost/core/key_sources/file_cache.py:40-47`: the new public `clear()` holds the real logic;
  `_clear()` was kept only so the two internal call sites inside `get()` (lines 22, 33) don't need
  a rename, and now reads `def _clear(self) -> None: self.clear()`. Either inline `self.clear()`
  at both call sites and delete `_clear`, or keep only the private method and make it public by
  rename — having both a public and a trivial private alias is unnecessary indirection.
- **New unit tests reach into private methods to count calls (Priority: Low, informational).**
  `test_clear_registry_cache_forces_reload` and `test_clear_spec_cache_forces_reload`
  (`tests/test_key_sources_chain_coverage.py:186-240`) monkeypatch
  `EnvKeySource._read_registry_file` / `SecretStoreKeySource._read_spec_file` directly to count
  invocations, coupling the tests to private method names — a harmless rename of either method
  breaks these tests with a `monkeypatch` `AttributeError` rather than a meaningful assertion
  failure. This is consistent with existing repo convention (same pattern already used at
  `tests/test_encryption_migration.py:493` monkeypatching `_read_raw_environments`), so it's not a
  new smell introduced by this task — noted for completeness, not actionable on its own.

---

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| `MtimeFileCache.clear()` resets state and forces a fresh `loader()` call | Present (`test_mtime_file_cache_clear`) |
| `clear_registry_cache()` forces `EnvKeySource` to re-read the registry file | Present (`test_clear_registry_cache_forces_reload`) |
| `clear_spec_cache()` forces `SecretStoreKeySource` to re-read the spec file | Present (`test_clear_spec_cache_forces_reload`) |
| Errno-portable bind-error formatting (`errno.EADDRINUSE` symbolic, not literal `48`) | Present (`test_format_mcp_bind_error_addr_in_use`, `test_metrics_addr_in_use_message`) |
| Registry rotation + re-encrypt reflects the *new* active key id (CLI + service) | Present (`test_cli_re_encrypt_dry_run`, `test_cli_re_encrypt_dry_run_json_includes_reencrypt_stats`, `test_cli_re_encrypt_reports_reencrypt_stats`, `test_bulk_re_encrypt_dry_run_projects_active_kid`) |
| Plaintext-hidden re-encryption actually rewrites the file (mtime advances) | Present (`test_bulk_re_encrypt_does_not_skip_with_plaintext_hidden`) |
| **The original same-tick race itself** — two rapid registry rewrites *without* an explicit `clear_registry_cache()` call, proving `MtimeFileCache` returns the stale value (i.e. a test that would fail again if the manual `clear_registry_cache()` calls were accidentally deleted from the 4 fixed tests) | Missing — today's new tests verify the *escape hatch* works, not that its absence reproduces the original bug |
| `SecretStoreKeySource._read_spec_file` handling of syntactically-valid non-object JSON (list/string/number) — the new `isinstance` guard | Missing |
| `EnvKeySource._read_registry_file` handling of the same non-object JSON case (the still-unguarded sibling path — see Code Quality Issues) | Missing |
| `MtimeFileCache.get()`'s pre-existing `OSError` branch (file removed between `stat()` and cache read) in combination with the new `clear()` | Missing — behavior is inherited/unchanged, never independently exercised |

**Timeout marker review: NO BLOCKER.** All 5 touched test files declare a module-level
`pytestmark = pytest.mark.timeout(...)` and it is retained (only reordered relative to imports)
by this task's diff:

| File | Marker |
| ---- | ------ |
| `tests/test_encryption_migrate_cli.py` | `pytest.mark.timeout(60)` |
| `tests/test_encryption_migration.py` | `pytest.mark.timeout(120)` |
| `tests/test_key_sources_chain_coverage.py` | `pytest.mark.timeout(30)` |
| `tests/test_mcp_server_manager.py` | `pytest.mark.timeout(60)` |
| `tests/test_metrics_server_startup.py` | `pytest.mark.timeout(60)` |

The 3 new tests added to `test_key_sources_chain_coverage.py`
(`test_mtime_file_cache_clear`, `test_clear_registry_cache_forces_reload`,
`test_clear_spec_cache_forces_reload`) inherit the module-level `timeout(30)` — verified by
grep (marker declared once, before the new test definitions) and by the passing repro runs
below completing in low single-digit seconds, well under the marker.

---

## Performance Concerns

None material. `MtimeFileCache.clear()` / `clear_registry_cache()` / `clear_spec_cache()` are
O(1) attribute resets. The new autouse `_reset_key_source_caches` fixture in `tests/conftest.py`
adds two cheap function calls before and after **every** test in the whole suite — negligible per
test, but it is suite-wide overhead paid by tests that never touch key sources or encryption
(see Shortcuts Taken). The full 62-test repro subset consistently completed in 1.3-3.4s across 8
runs (see Test Results), so there is no observable regression from the added fixture or the
`os.utime` call.

---

## Test Results — Repro Validation (this step)

Repro command (exactly as given in the Jira description), run against the current working tree
(uncommitted PYPOST-1088 diff applied) with `.venv/bin/python -m pytest`:

```
pytest -q tests/test_encryption_migrate_cli.py tests/test_encryption_migration.py \
  tests/test_mcp_server_manager.py tests/test_metrics_server_startup.py
```

- Ran **8 times** total against the current working tree. All 4 originally-named node ids
  (`test_format_mcp_bind_error_addr_in_use`, `TestFormatBindError::test_metrics_addr_in_use_message`,
  `test_cli_re_encrypt_dry_run`, `test_bulk_re_encrypt_dry_run_projects_active_kid`) **passed in
  every run**, along with all other tests in `test_cli_re_encrypt_dry_run_json_includes_reencrypt_stats`
  / `test_cli_re_encrypt_reports_reencrypt_stats` / `test_bulk_re_encrypt_does_not_skip_with_plaintext_hidden`
  (the other 3 tests named in `20-architecture.md`'s "Affected Test Cases").
- Ran the encryption-only pair (`test_encryption_migrate_cli.py` + `test_encryption_migration.py`,
  no `-p no:randomly` needed — no random-order plugin is installed in `.venv`, confirmed via
  `pip list`) **5 additional times** in isolation: 42/42 passed every time, 0.10s each — root
  cause 2A/2B flakiness is resolved.
- 6/8 full-repro runs were 62/62 green. 2/8 runs showed exactly one failure, always
  `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed` — a test **not** among the
  4 originally-described node ids and **not modified** by this task's diff (diff review: only
  `test_format_mcp_bind_error_addr_in_use`, `test_set_variable_supplier_forwards_to_impl`,
  `test_set_hidden_keys_supplier_forwards_to_impl`, and an import cleanup in
  `test_run_uvicorn_drains_pending_task_without_destroyed_warning` were touched in that file).
- **Baseline cross-check:** built a throwaway `git worktree` at this task's pre-diff base commit
  (`3e4cc8b8`, current `HEAD`, no PYPOST-1088 changes applied) and re-ran the same commands there
  (isolating the worktree's own `pypost`/`tests` copies via `PYTHONPATH`, main working tree
  untouched throughout, worktree removed after). Baseline results:
  - `test_mcp_server_manager.py` + `test_metrics_server_startup.py` alone: 5/5 runs clean (20/20)
    — matches current-tree behavior for these two files in isolation.
  - Full 4-file repro command: **every one of 6 baseline runs failed**, with 2-5 failures per
    run scattered across `test_cli_re_encrypt_dry_run`, `test_cli_re_encrypt_dry_run_json_includes_reencrypt_stats`,
    `test_cli_re_encrypt_reports_reencrypt_stats`, `test_bulk_re_encrypt_dry_run_projects_active_kid`,
    and `test_bulk_re_encrypt_does_not_skip_with_plaintext_hidden` — confirming the pre-fix
    flakiness described in the Jira ticket at the exact severity described (which failure(s) hit
    varies run to run). This is strong, direct evidence Iteration 3's fix resolves root causes 2A/2B:
    same command, same machine, same load — 0/8 failures with the fix applied vs. 6/6 runs with
    at least one encryption-test failure without it.
  - Critically, baseline iteration 5 of the full 4-file repro **also failed**
    `test_mcp_server_manager.py::test_port_busy_emits_start_failed` — proving that flake predates
    this task's diff entirely and is unrelated to it (see NON-BLOCKER entry below).

**Conclusion:** root cause (1) (errno hardcoding) and root cause (2) (encryption-migration
test-order flakiness) are both fixed and hold up under repeated stress; the Definition of Done in
`10-requirements.md` is met for the 4 originally-named node ids. The `test_port_busy_emits_start_failed`
flake is a separate, pre-existing, out-of-scope defect (below).

---

## Follow-up Tasks

### TD-1 — Medium

- **Item:** Add the same `isinstance(data, dict) else None` guard that `secret_store.py`'s
  `_read_spec_file` gained in this task to the structurally identical
  `EnvKeySource._read_registry_file` (`pypost/core/key_sources/env.py:33-49`), and add one test
  per loader asserting a non-object JSON registry/spec file returns `None` instead of raising.
- **Notes:** Latent bug pre-dates PYPOST-1088 (out of its declared scope), but this task's diff
  made the asymmetry between the two sibling loaders worse by fixing only one side. Small, safe,
  well-isolated fix.
- **Jira:** [PYPOST-1112](https://pypost.atlassian.net/browse/PYPOST-1112) (2 SP)

### TD-2 — Medium

- **Item:** Make `MtimeFileCache` (or its call sites) structurally robust to same-filesystem-tick
  rewrites instead of relying on every caller to remember an explicit `clear()` call — e.g. an
  internal write-generation counter incremented by the writer on save, or switching the identity
  check to file content hash. Add a regression test that reproduces the original race (two rapid
  registry rewrites with no manual `clear_registry_cache()` call) to prove the fix holds
  structurally, not just at the 4 currently-patched call sites.
- **Notes:** This task's fix is a correct, narrowly-scoped point-fix (call `clear_registry_cache()`
  after each test's registry rewrite); this ticket is the deferred structural hardening flagged in
  `20-architecture.md`'s own risk framing ("mtime-based polling is optimal for production read
  paths... explicit cache invalidation entry points avoid test pollution") so any *new* test or
  script with the same shape doesn't reintroduce PYPOST-1088's exact symptom.
- **Jira:** [PYPOST-1114](https://pypost.atlassian.net/browse/PYPOST-1114) (5 SP)

### NON-BLOCKER — pre-existing (newly discovered during this Step 7 repro-validation stress run;
unrelated to PYPOST-1088's diff, confirmed via baseline `git worktree` at the pre-task commit)

- **Node ID:** `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed`
- **Details:** Intermittently fails with `assert statuses` / `E assert []` (line
  `tests/test_mcp_server_manager.py:60`). The test only waits for `manager.start_failed` to be
  emitted (`wait_until(lambda: bool(failures), ...)`, line 57) before asserting on `statuses`,
  which is populated by the separate `status_changed` Qt signal — a signal-ordering race under
  system load, not related to errno formatting or key-source caching. Observed 2/8 runs against
  the current working tree and 1/6 runs against the unmodified baseline worktree at commit
  `3e4cc8b8` — confirming it predates and is unrelated to this task's diff (the diff to
  `test_mcp_server_manager.py` never touches this test function).
- **Repro:** `pytest -q tests/test_encryption_migrate_cli.py tests/test_encryption_migration.py
  tests/test_mcp_server_manager.py tests/test_metrics_server_startup.py` (run several times; not
  reliably reproduced on the first try — observed rate here was roughly 1/4 to 1/6 runs).
- **Suggested fix (for whoever picks up the ticket):** extend the `wait_until` predicate to
  `lambda: bool(failures) and bool(statuses)` (or add a second bounded wait on `statuses`) before
  asserting on `statuses[-1]`.
- **Jira search performed:** `jira_search_issues_jql` for `test_port_busy_emits_start_failed` /
  `port_busy_emits_start_failed` / `MCPServerManager port-busy` found one related-but-distinct
  issue, **PYPOST-716** ("[PYPOST-686] Stabilize MCPServerManager port-busy test", status
  **Done**), which addressed a **macOS segfault** in this same test (root cause: mocking uvicorn
  bind / platform-skip pending PYPOST-429) — a different symptom than the Linux signal-ordering
  race observed here. No open issue covers this specific flake.
- **Jira:** [PYPOST-1113](https://pypost.atlassian.net/browse/PYPOST-1113) (2 SP)

---

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| Pytest Timeouts | Explicit timeout marker on all touched/added tests | PASS | All 5 touched files retain module-level `pytestmark`; 3 new tests inherit it |
| Test Suite (targeted) | 4 originally-named node ids pass reliably | PASS | 8/8 repro runs, 5/5 additional isolated runs — 0 failures |
| Test Suite (full repro) | No failure outside the documented pre-existing set | NON-BLOCKER | 2/8 runs hit 1 unrelated pre-existing flake (`test_port_busy_emits_start_failed`), confirmed pre-existing via baseline worktree, filed above |
| Static Analysis | Zero linter errors on touched files | PASS | Per Step 5 (`40-code-cleanup.md`); unchanged since, no code edited in this step |
| Architecture & DoD | Matches approved architecture | PASS (with 1 note) | `secret_store.py`'s `isinstance` guard is a small, unreviewed addition beyond the architecture doc's described diff — see Shortcuts Taken |
| Pre-existing failures | Filed or explicitly out of scope | NON-BLOCKER | 1 new pre-existing flake documented above with baseline evidence; not yet ticketed |
| **Verdict** | Step 7 gate readiness | **NO BLOCKER — proceed to Step 8** | Two Medium follow-ups (TD-1, TD-2) and one pre-existing flake recorded for future tickets; nothing here should hold up this task's own completion |
