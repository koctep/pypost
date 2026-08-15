# PYPOST-1006: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — no blockers. The three verification gaps from
PYPOST-987 follow-up #4 are locked in tests. No production code changed.
No new Jira follow-up is required from this ticket.

Scope reviewed: `tests/test_collections_import_ui.py`,
`tests/test_collection_import.py`, and `ai-tasks/PYPOST-1006/*`. Production
modules were read only to confirm the tests observe the intended seams.

## Shortcuts Taken

None that compromise the lock. This is test-only verification debt.

- **No production change.** Invalid-file WARNING reasons, the apply-to-all
  loop, and `plan_collection_import` / `keep_both` copy naming were already
  correct. Step 3 tests went green immediately, as architecture predicted.
- **One well-chosen case per gap**, not a parametrize matrix. Architecture
  called this sufficient: 3 names (not 2), KEEP_BOTH (not SKIP), and copy
  `(3)` when `Copy of X` and `Copy of X (2)` are taken. That matches the
  combinatorial N+1 intent without extra fixtures.
- **Dedicated caplog tests** rather than extending the two existing
  invalid-file UX tests. Existing tests stay as dialog/state locks; the new
  pair owns the log contract (same split as
  `test_logs_completed_event_with_counts`).

## Code Quality Issues

- **KEEP_BOTH copy-name test repeats the first three names.** After asserting
  the full `result.collections` name list, it re-asserts
  `result.collections[:3]` names. Harmless duplication; not worth a
  follow-up.
- **3-conflict UI test asserts names, not existing ids.** A KEEP_BOTH loop
  that replaced an existing id but kept the same three originals plus three
  copies would still pass. The two-conflict SKIP test already locks
  identity (`["c1", "c2"]`). Adding ids here would be polish, not a gap in
  the apply-to-all proof (`called_once`, `remaining_count == 2`, third copy
  present).
- **Zero-usable caplog test does not mutually exclude the parse-fail
  reason.** The parse-fail test asserts no `reason=no_valid_collections`.
  The empty-list test asserts the exact token
  `collection_import_file_invalid reason=no_valid_collections` (and
  orchestrator logger / WARNING). That already distinguishes the branches.
  Mirroring the negative assert is optional symmetry.

None of these are production defects or incomplete DoD.

## Missing Tests

**No blocker.** Explicit timeouts per `.cursor/lsr/do-testing.md`:

- `tests/test_collection_import.py` —
  `pytestmark = pytest.mark.timeout(30)` (pure-unit). New KEEP_BOTH test
  inherits it.
- `tests/test_collections_import_ui.py` —
  `pytestmark = pytest.mark.timeout(60)` (GUI / event-loop, default
  signal-based timeout, no `method="thread"`). New caplog and 3-conflict
  tests inherit it. Internal wait remains `_wait_import` →
  `process_until(..., timeout_ms=5000)`.

### Closed by this ticket (DoD)

- caplog `collection_import_file_invalid` on parse failure, with parse
  text, orchestrator logger, not `no_valid_collections` — present
- caplog same event with exact `reason=no_valid_collections` — present
- Invalid-file UX: error dialog + collections unchanged (both reasons) —
  present (pre-existing; still green)
- 3 distinct conflicts, KEEP_BOTH + apply-to-all, one prompt,
  `remaining_count == 2`, three copies — present
- Two-conflict apply-to-all SKIP (regression) — present (pre-existing)
- Collection-side KEEP_BOTH copy name past `(2)` → `(3)` — present
- In-file duplicates through `(2)` (regression) — present (pre-existing)

### Remaining gaps — already ticketed or explicitly out of scope

These are **not** new debt from PYPOST-1006. Do not re-ticket.

- **Environment-import combinatorial sibling** — 3+ apply-to-all and
  `generate_import_copy_name` past `(2)` on the environment side. Tracked as
  [PYPOST-1002](https://pypost.atlassian.net/browse/PYPOST-1002)
  (PYPOST-986 follow-up #4). This ticket locked the collection caller only.
- **Rename-summary undercount** —
  [PYPOST-1003](https://pypost.atlassian.net/browse/PYPOST-1003).
- **Import atomicity / reconcile** —
  [PYPOST-1004](https://pypost.atlassian.net/browse/PYPOST-1004) (shipped;
  remaining optional polish is on 1004 follow-ups).
- **Off-thread parse** —
  [PYPOST-1005](https://pypost.atlassian.net/browse/PYPOST-1005) (shipped).
  Tests here wait with `_wait_import`; they do not re-open that work.
- **mypy baseline keying** —
  [PYPOST-1007](https://pypost.atlassian.net/browse/PYPOST-1007).
- **Very-large-file import test** — recorded on PYPOST-987 as a separate
  missing-test note, not this follow-up. Parse is now off-thread
  (PYPOST-1005); optional real-parse / large JSON regression sits on
  [PYPOST-1063](https://pypost.atlassian.net/browse/PYPOST-1063), not here.
- **3+ apply-to-all OVERWRITE** — architecture required a decision that is
  not the planner default (KEEP_BOTH). OVERWRITE at N=3 is not a remaining
  DoD item.
- **Direct `generate_import_copy_name` unit test past `(2)` in the
  collection suite** — out of scope; that would test the shared helper,
  which environment tests own through `(2)` and PYPOST-1002 owns past it.

### Soft gaps from this change (no Jira)

- Mutual-exclusion assert on the zero-usable caplog test (see *Code Quality
  Issues*).
- Existing-id assertion on the 3-conflict UI test.

Neither fails the Definition of Done.

## Performance Concerns

None. Tests are hermetic, in-memory, and sub-second for the new cases. No
production path changed, so import latency for users is unchanged.

Full `make test` can still abort on macOS with a segfault in unrelated
encryption-migration UI tests (`test_reencrypt_runs_when_confirmed`). That
flake is pre-existing (see PYPOST-1004 / 1005 reports and
`doc/dev/testing.md`), not introduced here. Targeted collection-import
modules pass.

## Deviations from Initial Architecture

None. Delivery matches `20-architecture.md`:

- Caplog both invalid `reason`s in `TestImportCollections`, scoped to
  `_MODULE` at WARNING; worker `collection_import_parse_worker_failed`
  cannot satisfy the parse-fail assert (`r.name == _MODULE`).
- 3-name apply-to-all uses KEEP_BOTH, `assert_called_once`,
  `remaining_count == 2`.
- Copy past `(2)` goes through `plan_collection_import` KEEP_BOTH, not a
  direct helper import.
- Existing two-conflict SKIP and in-file `(2)` tests left as regression
  locks.
- No production API, log-format, conflict policy, or copy-name scheme
  change.

Dev-doc mention of the three locks in `doc/dev/collection_import.md` remains
**Step 8**, as planned.

## Hardcoded Values

None in production. Test fixtures reuse existing names (`My API`,
`Billing`, `Auth`, `API`) and the same parse-error text as the behavioral
invalid-file tests (`File is not valid JSON: boom`).

## Pre-existing Issues Encountered (not caused by this task)

- Full-suite macOS Qt segfault in encryption-migration UI tests (out of
  scope).
- Sibling PYPOST-987 follow-ups listed above remain on their own tickets.

## Follow-up Tasks

**None.** This ticket created no new work that still needs a Jira issue.

Already-ticketed siblings (PYPOST-1002, 1003, 1004, 1005, 1007, and
large-file PYPOST-1063) are **not** follow-ups of this change; they are
recorded under *Missing Tests* so they are not mistaken for new debt.

Step 8 of **this** task should note the three new locks in
`doc/dev/collection_import.md` if that file lists tests — documentation,
not a Debt issue.

## Verdict

**SAFE TO CLOSE** — no blockers. All new tests inherit explicit module
timeouts; both invalid-file `reason`s are asserted via caplog; 3+
apply-to-all KEEP_BOTH is locked; collection-side copy uniqueness past
`(2)` is locked. Remaining gaps are already ticketed elsewhere or
explicitly out of scope. No new follow-up Jira issue.
