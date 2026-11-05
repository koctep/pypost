# PYPOST-1324: Technical Debt Analysis

Scope analysed: working-tree changes that make connected-library import
interruptible —
`pypost/core/qt/library_operation_worker.py`,
`pypost/core/library_collection_import.py`,
`pypost/ui/presenters/collection_import_actions.py`,
`pypost/core/metrics_registry.py`,
`tests/test_library_operation_interrupt_repro.py` (new),
updated teardown budget / policy / main-window shutdown repros, and prior-step
artifacts. Closes PYPOST-1264 Risk 4 / follow-up 3 (join-only library P3).

**Timeout markers (do-testing BLOCKER check): no blocker.** New and touched
modules declare explicit timeouts:

| Module | Marker |
| --- | --- |
| `tests/test_library_operation_interrupt_repro.py` | `pytestmark = pytest.mark.timeout(30)` |
| `tests/test_collection_import_teardown_budget_repro.py` | `pytestmark = pytest.mark.timeout(30)` |
| `tests/test_collection_import_teardown_policy.py` | `pytestmark = pytest.mark.timeout(30)` |
| `tests/test_main_window_collections_shutdown_repro.py` | `pytestmark = pytest.mark.timeout(30)` |

Internal waits use bounded `Event.wait` / `QThread.wait(ms)` /
`deadline.bounded(final_join_ms)`. Honoring-path wall assert uses
`_HONORING_ELAPSED_LIMIT_MS = 400`; unclean guard uses loose `< 2B`.

Phase D / tech-debt-jira-sync creates Debt issues for **new** follow-ups below;
this step only records candidates. Pre-existing suite failures already ticketed
in Step 4 triage keep their browse links.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | Medium | No unit tests for `list_entries` / `resolve_entries` cancel checkpoints | yes (new) |
| TD-2 | Low | Dev docs still describe join-only library P3 / Risk 4 | addressed in Step 8 |
| TD-3 | Low | `cancellation_token: Any` in actions instead of `CancellationToken` | yes (new) |
| TD-4 | Low | `AttributeError` on `operation_cancelled.disconnect` for spy doubles | yes (new) |
| TD-5 | Low | Library presenter still has no cancel/teardown interrupt path | yes (new; accepted DoD 6 residual) |
| TD-6 | Lowest | Shared `final_join_ms` for file + library (no separate knob) | no unless measured |
| TD-7 | Lowest | Mid-I/O cancel still impossible inside `find_and_read_manifest` / load | no (accepted NFR) |
| TD-8 | — | Pre-existing / flaky suite failures from Step 4 triage | already ticketed |

## Shortcuts Taken

1. **Developer docs deferred to Step 8 (now updating).**
   `doc/dev/collection_import.md` previously documented join-only P3
   (`wait(remaining)`, “library worker cannot be interrupted”, Risk 4). Step 6
   flagged the mismatch (`phase=`, cancelled join fields, metrics `cancelled`).
   Step 8 updates that file; see TD-2.

2. **Reuse `final_join_ms` for library post-disconnect join.**
   Architecture / requirements explicitly chose one documented grace for file and
   library rather than a second policy field. Acceptable until latency evidence
   demands `library_final_join_ms`. See TD-6.

3. **Teardown / e2e repros use synthetic ops and spy workers, not live library I/O.**
   Test A spies `cancel`/`wait`; Test B / unclean guard inject cancel-aware or
   cancel-ignoring callables via `_start_library_operation`. That matches the
   Step 2 red-repro plan and avoids network/disk roots, but does not exercise
   production `list_entries` / `resolve_entries` checkpoint loops. See TD-1.

4. **`AttributeError` retained when disconnecting `operation_cancelled`.**
   Spy library workers in older budget/shutdown doubles historically lacked the
   signal; production `LibraryOperationWorker` always has it. The extra except
   arm is a temporary compatibility shim. See TD-4.

5. **Library presenter product cancel left untouched (DoD 6).**
   Shared runner now exposes `cancel()` + `operation_cancelled`; MCP’s existing
   `_cancel_worker` gains a real cooperative stop. Inventing Library Manager
   close/cancel UX was out of scope. Residual: presenter `run_operation_async`
   still abandons in-flight work without `cancel()` on panel close. See TD-5.

6. **Coarse cooperative checkpoints only.**
   Cancel is observed between connections / declared paths / selected entries /
   materialize candidates — not inside a single `find_and_read_manifest` or
   `load_collection_import_candidates` call. Matches requirements NFR /
   architecture Risk 1. See TD-7.

## Code Quality Issues

1. **TD-3 (Low) — loose typing on cancel kwargs in actions.**
   `_resolve_operation` and `_resolve_library_candidates` annotate
   `cancellation_token: Any | None` instead of importing
   `CancellationToken`. Works with `call_with_cancellation_token` duck-typing
   and avoids a circular-import fear, but weakens static checks versus
   `LibraryCollectionImportService` which uses the real type. Prefer matching
   the service signature.

2. **TD-4 (Low) — `AttributeError` disconnect guard.**
   P3 disconnects `operation_completed` / `failed` / `cancelled` / `finished`
   with `(RuntimeError, TypeError)` for Qt/spy cases, plus `AttributeError` only
   for `operation_cancelled`. Once all test doubles expose the signal (or use a
   shared spy base), drop `AttributeError` so missing wiring fails loudly.

3. **Worker cancel flag triad mirrors siblings, slightly redundant.**
   `LibraryOperationWorker` keeps `_cancelled`, Qt interruption, and CTS —
   same shape as ManifestDiscoveryWorker / CollectionFetchWorker. Post-success
   checks of `_cancelled or isInterruptionRequested()` correctly suppress
   late `operation_completed` when cancel raced the return. Not worth a
   follow-up unless consolidating worker cancel helpers later.

4. **Broad `except Exception` → `operation_cancelled` when cancel was requested.**
   If the op raises a real error after `cancel()`, the worker emits cancelled
   rather than failed. Quiet teardown is correct; a rare diagnostic gap if a
   true failure coincides with cancel. Matches sibling cancel-over-failure
   preference; no separate ticket.

5. **No unexplained architecture deviation.**
   CTS + `cancel()` (not bare interrupt), `call_with_cancellation_token`,
   resolution nested `def` accepting `cancellation_token=`, P0/P3 `cancel()` +
   `bounded(final_join_ms)`, `operation_cancelled` → IDLE, metrics
   `outcome=cancelled` — all match Step 2.

## Missing Tests

1. **TD-1 (Medium) — service-level cancel checkpoint unit tests.**
   No focused test that:
   - `list_entries(..., cancellation_token=cancelled)` stops between connections
     or declared paths without finishing the full inventory;
   - `resolve_entries(..., cancellation_token=cancelled)` stops between selected
     entries;
   - materialize loop in `_resolve_library_candidates` raises
     `OperationCancelledError` between candidates.
   Teardown contract is covered (Test A/B + unclean + policy/budget/shutdown
   updates). Service hooks are regression-vulnerable without a small Qt-free
   unit module using a fake manager / stubbed load helpers.

2. **No live connected-library root in the interrupt suite.**
   Accepted shortcut (architecture: no live external deps for primary red).
   Optional later: one integration that cancels during real listing against a
   temp library fixture — only if TD-1 unit coverage proves insufficient.

3. **Otherwise covered for this task:**
   - P3 `cancel()` before wait and `wait_ms <= final_join_ms` (Test A + budget spies)
   - Cancel-honoring clean teardown, token observed, no late completed (Test B)
   - Cancel-ignoring unclean within `< 2B`
   - Main-window shutdown owner asserts library `cancels >= 1`
   - Caplog `phase=p0` / `phase=p3`, cancelled join `wait_ms`/`elapsed_ms`,
     metrics `cancelled` allowlist
   - Explicit timeouts on all touched modules (no blocker)

## Performance Concerns

1. **Worst-case library join is now short after stop is requested.**
   Pre-change: P3 could burn the entire remaining collections share.
   Post-change: P3 is `min(final_join_ms, remaining)` after `cancel()`. When
   cancellation is honored during P0/P1, P3 often finds the worker already idle
   (no join cost). Net improvement; no new ticket.

2. **Unclean path still abandons a running thread after the bounded join.**
   Same cooperative-only contract as file parse; stuck syscall past
   `final_join_ms` yields unclean and leaves the thread until it exits.
   Accepted (TD-7 / architecture Risk 1).

3. **Double `cancel()` (P0 + P3) is cheap.**
   Second cancel on an already-cancelled CTS is intentional safety for workers
   still running after wait-idle. Negligible cost.

4. **Idle / no-library teardown unchanged** — no added delay when no library
   worker is active.

## Follow-up Tasks

Specific tasks for Phase D / tech-debt Jira sync (do **not** create issues in
Step 7). Leave Jira empty for new items until ticketed.

1. **TD-1 — Add Qt-free unit tests for library import cancel checkpoints**
   (`list_entries` / `resolve_entries` loop boundaries and
   `_resolve_library_candidates` materialize loop). Priority: **Medium**.
   Jira: [PYPOST-1494](https://pypost.atlassian.net/browse/PYPOST-1494).

2. **TD-2 — Update `doc/dev/collection_import.md`** for interrupt-then-bounded
   library P3 (`cancel()` + `final_join_ms`), retire Risk 4 / join-only wording,
   document `phase=p0|p3`, cancelled join fields, and metrics `cancelled`.
   Priority: **Low** — addressed in Step 8 of this task
   (`doc/dev/collection_import.md`).
   Jira: _(none — Step 8 of PYPOST-1324)_

3. **TD-3 — Type `cancellation_token` as `CancellationToken | None`** in
   `CollectionImportActions` resolution helpers (match the service API).
   Priority: **Low**.
   Jira: [PYPOST-1495](https://pypost.atlassian.net/browse/PYPOST-1495).

4. **TD-4 — Drop `AttributeError` from `operation_cancelled.disconnect`** once
   test spies always expose the signal (shared spy helper). Priority: **Low**.
   Jira: [PYPOST-1496](https://pypost.atlassian.net/browse/PYPOST-1496).

5. **TD-5 — Optional LibraryPresenter close/teardown cooperative cancel** for
   in-flight `run_operation_async` workers (product UX still out of
   PYPOST-1324 scope). Priority: **Low**.
   Jira: [PYPOST-1497](https://pypost.atlassian.net/browse/PYPOST-1497).

Already-ticketed residual closed by this task (pointer only; do not re-file):

6. **Make `LibraryOperationWorker` interruptible** —
   [PYPOST-1324](https://pypost.atlassian.net/browse/PYPOST-1324) (this issue;
   was PYPOST-1321 follow-up 5 / PYPOST-1264 Risk 4).

Accepted / no new ticket:

7. **TD-6 — Shared `final_join_ms`** — revisit only if measurement shows library
   exit needs a different grace than file parse.
8. **TD-7 — Mid-syscall cancel** — cooperative checkpoints only; unclean within
   budget remains the escape hatch.

### Pre-existing suite failures (Step 4 triage; Step 7 retain)

Recorded during development against base `4a40ff6b`. Unrelated to library
interruptibility. Verdict for all: **`NON-BLOCKER — pre-existing`** (or flaky
as noted). Do not re-file.

| Test ids | Verdict | Jira |
| --- | --- | --- |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples`; `tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | NON-BLOCKER — pre-existing (fails at base `4a40ff6b`) | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_pypost_1077_verification_votes.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`; `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | NON-BLOCKER — pre-existing (fails at base `4a40ff6b`) | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | NON-BLOCKER — pre-existing / env drift (`requirements-dev.txt` stale vs `.in`; baseline isolation can pass) | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) |
| `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` | NON-BLOCKER — pre-existing (fails at base `4a40ff6b`; mixins.py 1053 vs 1055) | [PYPOST-1492](https://pypost.atlassian.net/browse/PYPOST-1492) |
| `tests/test_mcp_stdio_harness.py::test_harness_stderr_collection` | NON-BLOCKER — flaky (failed in suite, passed re-run + baseline) | [PYPOST-1493](https://pypost.atlassian.net/browse/PYPOST-1493) |

No BLOCKER debt. Medium item TD-1 is hardening coverage for service checkpoints
already wired in production. TD-2 docs drift is cleared in Step 8
(`doc/dev/collection_import.md`).
